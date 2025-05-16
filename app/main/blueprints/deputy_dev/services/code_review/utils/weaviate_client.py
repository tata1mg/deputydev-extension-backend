from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.services.initialization.review_initialization_manager import ReviewInitialisationManager
from deputydev_core.utils.weaviate import weaviate_connection
from deputydev_core.services.repository.dataclasses.main import (
    WeaviateSyncAndAsyncClients,
)
from typing import Optional
from sanic import Sanic


class ReviewWeaviateSyncAndAsyncClients(WeaviateSyncAndAsyncClients):
    """Enhanced Weaviate client with additional functionality for reconnection and initialization."""

    async def ensure_connected(self):
        """Ensures connection to Weaviate is established, reinitializing if necessary."""
        if not await self.is_ready():
            weaviate_client = await ReviewInitialisationManager().initialize_vector_db()
            self.sync_client = weaviate_client.sync_client
            self.async_client = weaviate_client.async_client


async def get_weaviate_connection() -> Optional[ReviewWeaviateSyncAndAsyncClients]:
    """
    Get or initialize Weaviate connection.

    Returns:
        Optional[EnhancedWeaviateClient]: The Weaviate client instance if successful, None otherwise.
    """
    try:
        app = Sanic.get_app()

        existing_client = await weaviate_connection()

        if existing_client:
            weaviate_client = existing_client
        else:
            new_weaviate_client = await ReviewInitialisationManager().initialize_vector_db()
            weaviate_client = ReviewWeaviateSyncAndAsyncClients(
                async_client=new_weaviate_client.async_client,
                sync_client=new_weaviate_client.sync_client,
            )

        app.ctx.weaviate_client = weaviate_client

        return weaviate_client

    except Exception as ex:
        AppLogger.log_error(f"Failed to get Weaviate connection: {ex}")
        return None
