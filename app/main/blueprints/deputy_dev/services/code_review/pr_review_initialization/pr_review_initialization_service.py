import asyncio
import traceback
from concurrent.futures import ProcessPoolExecutor

from deputydev_core.services.initialization.review_initialization_manager import (
    ReviewInitialisationManager,
    WeaviateSyncAndAsyncClients,
)
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.constants.enums import ContextValueKeys

from app.main.blueprints.deputy_dev.client.one_dev_review_client import (
    OneDevReviewClient,
)
from app.main.blueprints.deputy_dev.services.code_review.utils.weaviate_client import ReviewWeaviateSyncAndAsyncClients
from sanic import Sanic
from app.main.blueprints.deputy_dev.services.code_review.utils.weaviate_client import get_weaviate_connection


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
        app = Sanic.get_app()
        if not hasattr(app.ctx, "weaviate_client"):
            return False
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
                    existing_client: WeaviateSyncAndAsyncClients = app.ctx.weaviate_client
                    await existing_client.async_client.close()
                    existing_client.sync_client.close()
                    new_weaviate_client = await ReviewInitialisationManager().initialize_vector_db()

                    app.ctx.weaviate_client = ReviewWeaviateSyncAndAsyncClients(
                        async_client=new_weaviate_client.async_client,
                        sync_client=new_weaviate_client.sync_client,
                    )

                    await new_weaviate_client.ensure_connected()
            except Exception as ex:
                AppLogger.log_error(f"Failed to maintain weaviate heartbeat: {ex}")
            await asyncio.sleep(3)

    @classmethod
    async def initialization(cls):
        app = Sanic.get_app()
        if not hasattr(app.ctx, "weaviate_client"):
            weaviate_client = await ReviewInitialisationManager().initialize_vector_db()

            app.ctx.weaviate_client = ReviewWeaviateSyncAndAsyncClients(
                async_client=weaviate_client.async_client,
                sync_client=weaviate_client.sync_client,
            )
            asyncio.create_task(cls.maintain_weaviate_heartbeat())

    @classmethod
    async def create_embedding(cls, repo_path):
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
                weaviate_client = await get_weaviate_connection()

                if weaviate_client:
                    initialisation_manager.weaviate_client = weaviate_client
                await initialisation_manager.initialize_vector_db()

                await initialisation_manager.prefill_vector_store(
                    chunkable_files_and_hashes=chunkable_files_and_hashes,
                )
        except Exception as ex:
            AppLogger.log_error(traceback.format_exc())
            print(f"embedding failed due to {ex}")
