import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional, Type

from prompt_toolkit.shortcuts.progress_bar import ProgressBar
from weaviate import WeaviateAsyncClient, WeaviateClient
from weaviate.connect import ConnectionParams, ProtocolParams
from weaviate.embedded import EmbeddedOptions

from app.common.models.dao.weaviate.base import Base as WeaviateBaseDAO
from app.common.models.dao.weaviate.chunk_files import ChunkFiles
from app.common.models.dao.weaviate.chunks import Chunks
from app.common.services.chunking.vector_store.cleanup import (
    ChunkVectorStoreCleaneupManager,
)
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repo.local_repo.factory import LocalRepoFactory
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger
from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.deputydev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.deputydev_cli.app.managers.chunking.chunker.handlers.one_dev_cli_chunker import (
    OneDevCLIChunker,
)
from app.main.blueprints.deputydev_cli.app.managers.embedding.embedding_manager import (
    OneDevEmbeddingManager,
)
from app.main.blueprints.deputydev_cli.app.repository.weaaviate_schema_details.weaviate_schema_details_service import (
    WeaviateSchemaDetailsService,
)
from app.main.blueprints.deputydev_cli.models.weaviate.weaviate_schema_details import (
    WeaviateSchemaDetails,
)
from app.main.blueprints.deputydev_cli.versions import WEAVIATE_SCHEMA_VERSION


class InitializationManager:
    def __init__(
        self,
        repo_path: str,
        auth_token: str,
        process_executor: ProcessPoolExecutor,
        one_dev_client: OneDevClient,
        weaviate_client: Optional[WeaviateSyncAndAsyncClients] = None,
    ) -> None:
        self.repo_path = repo_path
        self.weaviate_client: Optional[WeaviateSyncAndAsyncClients] = weaviate_client
        self.local_repo = None
        self.embedding_manager = OneDevEmbeddingManager(auth_token=auth_token, one_dev_client=one_dev_client)
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

        if not self.weaviate_client:
            raise ValueError("Connect to vector store failed")

        schema_version = WeaviateSchemaDetailsService(weaviate_client=self.weaviate_client).get_schema_version()

        is_schema_invalid = schema_version is None or schema_version != WEAVIATE_SCHEMA_VERSION

        if should_clean or is_schema_invalid:
            AppLogger.log_debug("Cleaning up the vector store")
            self.weaviate_client.sync_client.collections.delete_all()

        await asyncio.gather(
            *[
                self.__check_and_initialize_collection(collection=Chunks),
                self.__check_and_initialize_collection(collection=ChunkFiles),
                self.__check_and_initialize_collection(collection=WeaviateSchemaDetails),
            ]
        )

        if is_schema_invalid:
            WeaviateSchemaDetailsService(weaviate_client=self.weaviate_client).set_schema_version(
                WEAVIATE_SCHEMA_VERSION
            )

        return self.weaviate_client

    async def prefill_vector_store(
        self, chunkable_files_and_hashes: Dict[str, str], progressbar: Optional[ProgressBar] = None
    ) -> None:
        if not self.local_repo:
            raise ValueError("Local repo is not initialized")

        if not self.weaviate_client:
            raise ValueError("Connect to vector store")

        all_chunks, _all_docs = await OneDevCLIChunker(
            local_repo=self.local_repo,
            weaviate_client=self.weaviate_client,
            embedding_manager=self.embedding_manager,
            process_executor=self.process_executor,
            progress_bar=progressbar,
            chunkable_files_and_hashes=chunkable_files_and_hashes,
        ).create_chunks_and_docs()

        # start chunk cleanup
        self.chunk_cleanup_task = asyncio.create_task(
            ChunkVectorStoreCleaneupManager(
                exclusion_chunk_hashes=[chunk.content_hash for chunk in all_chunks],
                weaviate_client=self.weaviate_client,
            ).start_cleanup_for_chunk_and_hashes()
        )

    async def cleanup(self):
        if self.chunk_cleanup_task:
            self.chunk_cleanup_task.cancel()
        if self.weaviate_client:
            self.weaviate_client.sync_client.close()
            await self.weaviate_client.async_client.close()
