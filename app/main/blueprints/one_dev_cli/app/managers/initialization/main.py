import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Type

from prompt_toolkit.shortcuts.progress_bar import ProgressBar
from weaviate import WeaviateAsyncClient
from weaviate.connect import ConnectionParams, ProtocolParams
from weaviate.embedded import EmbeddedOptions

from app.common.models.dao.weaviate.base import Base as WeaviateBaseDAO
from app.common.models.dao.weaviate.chunk_files import ChunkFiles
from app.common.models.dao.weaviate.chunks import Chunks
from app.common.services.chunking.chunking_handler import source_to_chunks
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repo.local_repo.factory import LocalRepoFactory
from app.main.blueprints.one_dev_cli.app.managers.embedding.embedding_manager import (
    OneDevEmbeddingManager,
)


class InitializationManager:
    def __init__(self, repo_path: str, auth_token: str, process_executor: ProcessPoolExecutor) -> None:
        self.repo_path = repo_path
        self.weaviate_client: Optional[WeaviateAsyncClient] = None
        self.local_repo = None
        self.embedding_manager = OneDevEmbeddingManager(auth_token=auth_token)
        self.process_executor = process_executor

    def get_local_repo(self) -> BaseLocalRepo:
        self.local_repo = LocalRepoFactory.get_local_repo(self.repo_path)
        return self.local_repo

    async def __check_and_initialize_collection(self, collection: Type[WeaviateBaseDAO]) -> None:
        if not self.weaviate_client:
            raise ValueError("Weaviate client is not initialized")
        exists = await self.weaviate_client.collections.exists(collection.collection_name)
        if not exists:
            await self.weaviate_client.collections.create(
                name=collection.collection_name,
                properties=collection.properties,
            )

    async def initialize_vector_db(self) -> WeaviateAsyncClient:
        if self.weaviate_client:
            return self.weaviate_client

        try:
            client = WeaviateAsyncClient(
                embedded_options=EmbeddedOptions(
                    hostname="127.0.0.1",
                    port=8079,
                    grpc_port=50050,
                    version="1.27.0",
                    additional_env_vars={
                        "LOG_LEVEL": "panic",
                    },
                ),
            )
            await client.connect()
            self.weaviate_client = client
        except Exception as _ex:
            if (
                "Embedded DB did not start because processes are already listening on ports http:8079 and grpc:50050"
                in str(_ex)
            ):
                client = WeaviateAsyncClient(
                    connection_params=ConnectionParams(
                        http=ProtocolParams(
                            host="127.0.0.1",
                            port=8079,
                            secure=False,
                        ),
                        grpc=ProtocolParams(
                            host="127.0.0.1",
                            port=50050,
                            secure=False,
                        ),
                    )
                )
                await client.connect()
                self.weaviate_client = client

        await asyncio.gather(
            *[
                self.__check_and_initialize_collection(collection=Chunks),
                self.__check_and_initialize_collection(collection=ChunkFiles),
            ]
        )

        return self.weaviate_client

    async def prefill_vector_store(self, progressbar: Optional[ProgressBar] = None) -> None:
        if not self.local_repo:
            raise ValueError("Local repo is not initialized")

        if progressbar:
            self.embedding_manager.progressbar = progressbar

        await source_to_chunks(
            local_repo=self.local_repo,
            weaviate_client=self.weaviate_client,
            embedding_manager=self.embedding_manager,
            process_executor=self.process_executor,
        )

    async def cleanup(self):
        if self.weaviate_client:
            await self.weaviate_client.close()
