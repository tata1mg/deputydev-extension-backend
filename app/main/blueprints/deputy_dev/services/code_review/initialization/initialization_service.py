import asyncio
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional

from deputydev_core.services.auth_token_storage.auth_token_service import (
    AuthTokenService,
)
# from deputydev_core.services.initialization.extension_initialisation_manager import (
#     ExtensionInitialisationManager,
#     WeaviateSyncAndAsyncClients
# )
from deputydev_core.services.initialization.review_initialization_manager import ReviewInitialisationManager, WeaviateSyncAndAsyncClients
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.auth import AuthStatus
from deputydev_core.utils.constants.enums import SharedMemoryKeys
from deputydev_core.utils.context_vars import get_context_value
from deputydev_core.utils.custom_progress_bar import CustomProgressBar
from deputydev_core.utils.shared_memory import SharedMemory
from sanic import Sanic
from app.backend_common.services.embedding.openai_embedding_manager import (
    OpenAIEmbeddingManager,
)
from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo

from app.main.blueprints.deputy_dev.client.one_dev_review_client import OneDevReviewClient


# from app.models.dtos.update_vector_store_params import UpdateVectorStoreParams
# from app.services.shared_chunks_manager import SharedChunksManager
# from app.utils.constants import Headers
# from app.utils.util import weaviate_connection
from deputydev_core.services.shared_chunks.shared_chunks_manager import SharedChunksManager


class InitializationService:

    @classmethod
    async def _monitor_embedding_progress(cls, progress_bar, progress_callback):
        """A separate task that can monitor and report progress while chunking happens"""
        try:
            while True:
                if not progress_bar.is_completed():
                    await progress_callback(progress_bar.total_percentage)
                else:
                    return
                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            return


    @classmethod
    async def is_weaviate_ready(cls) -> bool:
        app = Sanic.get_app()
        if not hasattr(app.ctx, "weaviate_client"):
            return False
        else:
            existing_client: WeaviateSyncAndAsyncClients = app.ctx.weaviate_client
            return await existing_client.is_ready()

    @classmethod
    async def maintain_weaviate_heartbeat(cls):
        while True:
            try:
                is_reachable = await cls.is_weaviate_ready()
                if not is_reachable:
                    AppLogger.log_info(f"Is Weaviate reachable: {is_reachable}")
                    app = Sanic.get_app()
                    existing_client: WeaviateSyncAndAsyncClients = (
                        app.ctx.weaviate_client
                    )
                    await existing_client.async_client.close()
                    existing_client.sync_client.close()
                    await existing_client.ensure_connected()
            except Exception:
                AppLogger.log_error("Failed to maintain weaviate heartbeat")
            await asyncio.sleep(3)

    @classmethod
    async def initialization(cls):
        class ReviewWeaviateSyncAndAsyncClients(WeaviateSyncAndAsyncClients):
            async def ensure_connected(self):
                if not await self.is_ready():

                    weaviate_client = (
                        await ReviewInitialisationManager().initialize_vector_db()
                    )
                    self.sync_client = weaviate_client.sync_client
                    self.async_client = weaviate_client.async_client

        app = Sanic.get_app()
        if not hasattr(app.ctx, "weaviate_client"):
            weaviate_client = (
                await ReviewInitialisationManager().initialize_vector_db()
            )
            app.ctx.weaviate_client = ReviewWeaviateSyncAndAsyncClients(
                async_client=weaviate_client.async_client,
                sync_client=weaviate_client.sync_client,
            )
            asyncio.create_task(cls.maintain_weaviate_heartbeat())

    # @classmethod
    # async def get_config(cls, base_config: Dict = {}) -> None:
    #     time_start = time.perf_counter()
    #     if not ConfigManager.configs:
    #         ConfigManager.initialize(in_memory=True)
    #         one_dev_client = OneDevClient(base_config)
    #         await one_dev_client.close_session()
    #         try:
    #             configs: Optional[Dict[str, str]] = await one_dev_client.get_configs(
    #                 headers={
    #                     "Content-Type": "application/json",
    #                     "Authorization": f"Bearer {SharedMemory.read(SharedMemoryKeys.EXTENSION_AUTH_TOKEN.value)}",
    #                 }
    #             )
    #             if configs is None:
    #                 raise Exception("No configs fetched")
    #             ConfigManager.set(configs)
    #             # SharedMemory.create(SharedMemoryKeys.BINARY_CONFIG.value, configs)
    #         except Exception as error:
    #             AppLogger.log_error(f"Failed to fetch configs: {error}")
    #             await cls.close_session_and_exit(one_dev_client)
    #
    #     time_end = time.perf_counter()
    #     AppLogger.log_info(f"Time taken to fetch configs: {time_end - time_start}")

    @staticmethod
    async def close_session_and_exit(one_dev_client):
        AppLogger.log_info("Exiting ...")
        await one_dev_client.close_session()


    @classmethod
    async def create_embedding(cls, repo_path, repo_service):
        try:
            print(f"Embedding started for repo {repo_path} started")

            with ProcessPoolExecutor(
                    max_workers=1
            ) as executor:
                one_dev_client = OneDevReviewClient()
                initialisation_manager = ReviewInitialisationManager(
                    repo_path=repo_path,
                    process_executor=executor,
                    one_dev_client=one_dev_client

                )
                local_repo = initialisation_manager.get_local_repo()
                chunkable_files_and_hashes = (
                    await local_repo.get_chunkable_files_and_commit_hashes()
                )
                await SharedChunksManager.update_chunks(
                    repo_path, chunkable_files_and_hashes
                )
                weaviate_client = await weaviate_connection()

                if weaviate_client:
                    initialisation_manager.weaviate_client = weaviate_client
                else:
                    await initialisation_manager.initialize_vector_db()

                await initialisation_manager.prefill_vector_store(
                    chunkable_files_and_hashes=chunkable_files_and_hashes,
                )
        except Exception as ex:
            AppLogger.log_error(traceback.format_exc())
            print(f"embedding failed due to {ex}")

async def weaviate_connection():
    app = Sanic.get_app()
    if app.ctx.weaviate_client:
        weaviate_clients: WeaviateSyncAndAsyncClients = app.ctx.weaviate_client
        if not weaviate_clients.async_client.is_connected():
            print(f"Async Connection was dropped, Reconnecting")
            await weaviate_clients.async_client.connect()
        if not weaviate_clients.sync_client.is_connected():
            print(f"Sync Connection was dropped, Reconnecting")
            weaviate_clients.sync_client.connect()
        return weaviate_clients


