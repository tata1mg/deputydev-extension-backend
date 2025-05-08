import asyncio
import traceback
from concurrent.futures import ProcessPoolExecutor

from deputydev_core.services.initialization.review_initialization_manager import (
    ReviewInitialisationManager,
    WeaviateSyncAndAsyncClients,
)
from deputydev_core.services.shared_chunks.shared_chunks_manager import (
    SharedChunksManager,
)
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.constants.enums import ContextValueKeys
from deputydev_core.utils.context_value import ContextValue
from deputydev_core.utils.weaviate import weaviate_connection

from app.main.blueprints.deputy_dev.client.one_dev_review_client import (
    OneDevReviewClient,
)


class PRReviewInitializationService:
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
        weaviate_client: WeaviateSyncAndAsyncClients = ContextValue.get(ContextValueKeys.WEAVIATE_CLIENT.value)
        if not weaviate_client:
            return False
        return await weaviate_client.is_ready()

    @classmethod
    async def maintain_weaviate_heartbeat(cls):
        while True:
            try:
                is_reachable = await cls.is_weaviate_ready()
                if not is_reachable:
                    AppLogger.log_info(f"Is Weaviate reachable: {is_reachable}")
                    weaviate_client: WeaviateSyncAndAsyncClients = ContextValue.get(
                        ContextValueKeys.WEAVIATE_CLIENT.value
                    )
                    if weaviate_client:
                        await weaviate_client.async_client.close()
                        weaviate_client.sync_client.close()
                        await weaviate_client.ensure_connected()
            except Exception:
                AppLogger.log_error("Failed to maintain weaviate heartbeat")
            await asyncio.sleep(3)

    @classmethod
    async def initialization(cls):
        class ReviewWeaviateSyncAndAsyncClients(WeaviateSyncAndAsyncClients):
            async def ensure_connected(self):
                if not await self.is_ready():
                    (
                        weaviate_client,
                        _new_weaviate_process,
                        _schema_cleaned,
                    ) = await ReviewInitialisationManager().initialize_vector_db()
                    self.sync_client = weaviate_client.sync_client
                    self.async_client = weaviate_client.async_client

        if not ContextValue.get(ContextValueKeys.WEAVIATE_CLIENT.value):
            (
                weaviate_client,
                _new_weaviate_process,
                _schema_cleaned,
            ) = await ReviewInitialisationManager().initialize_vector_db()
            client_wrapper = ReviewWeaviateSyncAndAsyncClients(
                async_client=weaviate_client.async_client,
                sync_client=weaviate_client.sync_client,
            )
            ContextValue.set(ContextValueKeys.WEAVIATE_CLIENT.value, client_wrapper)
            asyncio.create_task(cls.maintain_weaviate_heartbeat())

    @classmethod
    async def create_embedding(cls, repo_path, repo_service):
        try:
            print(f"Embedding started for repo {repo_path} started")

            with ProcessPoolExecutor(max_workers=1) as executor:
                one_dev_client = OneDevReviewClient()
                initialisation_manager = ReviewInitialisationManager(
                    repo_path=repo_path,
                    process_executor=executor,
                    auth_token_key=ContextValueKeys.PR_REVIEW_TOKEN.value,
                    one_dev_client=one_dev_client,
                )
                local_repo = initialisation_manager.get_local_repo()
                chunkable_files_and_hashes = await local_repo.get_chunkable_files_and_commit_hashes()
                await SharedChunksManager.update_chunks(repo_path, chunkable_files_and_hashes)
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
