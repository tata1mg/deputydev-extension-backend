import asyncio
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Dict, Optional, Type

import xxhash
from prompt_toolkit.shortcuts.progress_bar import ProgressBar
from weaviate import WeaviateAsyncClient, WeaviateClient
from weaviate.connect import ConnectionParams, ProtocolParams
from weaviate.embedded import EmbeddedOptions

from app.common.models.dao.weaviate.base import Base as WeaviateBaseDAO
from app.common.models.dao.weaviate.chunk_files import ChunkFiles
from app.common.models.dao.weaviate.chunks import Chunks
from app.common.models.dao.weaviate.chunks_usages import ChunkUsages
from app.common.services.chunking.vector_store.cleanup import (
    ChunkVectorStoreCleaneupManager,
)
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repo.local_repo.factory import LocalRepoFactory
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.one_dev_cli.app.managers.chunking.chunking_handler import (
    OneDevCLIChunker,
)
from app.main.blueprints.one_dev_cli.app.managers.embedding.embedding_manager import (
    OneDevEmbeddingManager,
)


class InitializationManager:
    def __init__(
        self,
        repo_path: str,
        auth_token: str,
        process_executor: ProcessPoolExecutor,
        weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
    ) -> None:
        self.repo_path = repo_path
        self.weaviate_client: Optional[WeaviateSyncAndAsyncClients] = weaviate_client
        self.local_repo = None
        self.embedding_manager = OneDevEmbeddingManager(auth_token=auth_token)
        self.process_executor = process_executor
        self.chunk_cleanup_task = None

    def get_local_repo(self) -> BaseLocalRepo:
        self.local_repo = LocalRepoFactory.get_local_repo(self.repo_path)
        return self.local_repo

    async def __check_and_initialize_collection(self, collection: Type[WeaviateBaseDAO]) -> None:
        if not self.weaviate_client:
            raise ValueError("Weaviate client is not initialized")
        exists = await self.weaviate_client.async_client.collections.exists(collection.collection_name)
        if not exists:
            await self.weaviate_client.async_client.collections.create(
                name=collection.collection_name,
                properties=collection.properties,
                references=collection.references if hasattr(collection, "references") else None,  # type: ignore
            )

    async def initialize_vector_db_async(self) -> WeaviateAsyncClient:
        if self.weaviate_client and self.weaviate_client.async_client:
            return self.weaviate_client.async_client

        async_client: Optional[WeaviateAsyncClient] = None
        try:
            async_client = WeaviateAsyncClient(
                embedded_options=EmbeddedOptions(
                    hostname=ConfigManager.configs["WEAVIATE_HOST"],
                    port=ConfigManager.configs["WEAVIATE_HTTP_PORT"],
                    grpc_port=ConfigManager.configs["WEAVIATE_GRPC_PORT"],
                    version="1.27.0",
                    additional_env_vars={
                        "LOG_LEVEL": "panic",
                    },
                ),
            )
            await async_client.connect()
        except Exception as _ex:
            if (
                "Embedded DB did not start because processes are already listening on ports http:8079 and grpc:50050"
                in str(_ex)
            ):
                async_client = WeaviateAsyncClient(
                    connection_params=ConnectionParams(
                        http=ProtocolParams(
                            host=ConfigManager.configs["WEAVIATE_HOST"],
                            port=ConfigManager.configs["WEAVIATE_HTTP_PORT"],
                            secure=False,
                        ),
                        grpc=ProtocolParams(
                            host=ConfigManager.configs["WEAVIATE_HOST"],
                            port=ConfigManager.configs["WEAVIATE_GRPC_PORT"],
                            secure=False,
                        ),
                    )
                )
                await async_client.connect()

        if not async_client:
            raise Exception("async client not initialized")
        return async_client

    def initialize_vector_db_sync(self) -> WeaviateClient:
        if self.weaviate_client and self.weaviate_client.async_client:
            return self.weaviate_client.sync_client

        sync_client = WeaviateClient(
            connection_params=ConnectionParams(
                http=ProtocolParams(
                    host=ConfigManager.configs["WEAVIATE_HOST"],
                    port=ConfigManager.configs["WEAVIATE_HTTP_PORT"],
                    secure=False,
                ),
                grpc=ProtocolParams(
                    host=ConfigManager.configs["WEAVIATE_HOST"],
                    port=ConfigManager.configs["WEAVIATE_GRPC_PORT"],
                    secure=False,
                ),
            )
        )
        sync_client.connect()
        return sync_client

    async def initialize_vector_db(self, should_clean: bool = False) -> WeaviateSyncAndAsyncClients:
        if self.weaviate_client:
            return self.weaviate_client
        async_client = await self.initialize_vector_db_async()
        sync_client = self.initialize_vector_db_sync()

        self.weaviate_client = WeaviateSyncAndAsyncClients(
            async_client=async_client,
            sync_client=sync_client,
        )

        if should_clean:
            AppLogger.log_debug("Cleaning up the vector store")
            self.weaviate_client.sync_client.collections.delete_all()

        await asyncio.gather(
            *[
                self.__check_and_initialize_collection(collection=Chunks),
                self.__check_and_initialize_collection(collection=ChunkFiles),
                self.__check_and_initialize_collection(collection=ChunkUsages),
            ]
        )

        if not self.weaviate_client:
            raise ValueError("Connect to vector store failed")

        return self.weaviate_client

    async def prefill_vector_store(
        self, chunkable_files_and_hashes: Dict[str, str], progressbar: Optional[ProgressBar] = None
    ) -> str:
        if not self.local_repo:
            raise ValueError("Local repo is not initialized")

        if not self.weaviate_client:
            raise ValueError("Connect to vector store")

        usage_hash = xxhash.xxh64(
            str(
                {
                    "repo_path": self.repo_path,
                    "current_day_start_time": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                }
            )
        ).hexdigest()

        all_chunks, _all_docs = await OneDevCLIChunker(
            local_repo=self.local_repo,
            weaviate_client=self.weaviate_client,
            embedding_manager=self.embedding_manager,
            process_executor=self.process_executor,
            usage_hash=usage_hash,
            progress_bar=progressbar,
            chunkable_files_and_hashes=chunkable_files_and_hashes,
        ).create_chunks_and_docs()

        # start chunk cleanup
        self.chunk_cleanup_task = asyncio.create_task(
            ChunkVectorStoreCleaneupManager(
                exclusion_chunk_hashes=[chunk.content_hash for chunk in all_chunks],
                weaviate_client=self.weaviate_client,
                usage_hash=usage_hash,
            ).start_cleanup_for_chunk_and_hashes()
        )

        return usage_hash

    async def cleanup(self):
        if self.chunk_cleanup_task:
            self.chunk_cleanup_task.cancel()
        if self.weaviate_client:
            self.weaviate_client.sync_client.close()
            await self.weaviate_client.async_client.close()
