import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.common.services.repository.chunk.chunk_service import ChunkService
from app.common.services.repository.chunk_files.chunk_files_service import (
    ChunkFilesService,
)
from app.common.services.repository.chunk_usages.chunk_usages_service import (
    ChunkUsagesService,
)
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger


class ChunkVectorStoreCleaneupManager:
    def __init__(
        self,
        exclusion_chunk_hashes: List[str],
        weaviate_client: WeaviateSyncAndAsyncClients,
        usage_hash: Optional[str] = None,
    ):
        self.exclusion_chunk_hashes = exclusion_chunk_hashes
        self.weaviate_client = weaviate_client
        self.last_used_at_timedelta = timedelta(minutes=3)
        self.usage_hash = usage_hash

    async def _cleanup_chunk_and_chunk_files_objects(self, chunk_hashes_to_clean: List[str]) -> None:
        time_start = time.perf_counter()
        try:
            ChunkService(weaviate_client=self.weaviate_client).cleanup_old_chunks(
                chunk_hashes_to_clean=chunk_hashes_to_clean,
            )
            ChunkFilesService(weaviate_client=self.weaviate_client).cleanup_old_chunk_files(
                chunk_hashes_to_clean=chunk_hashes_to_clean,
            )
            AppLogger.log_debug(
                f"Cleaning up {len(chunk_hashes_to_clean)} chunks took {time.perf_counter() - time_start} seconds"
            )
        except Exception as _ex:
            AppLogger.log_debug(message=str(_ex))

    async def start_cleanup_for_chunk_and_hashes(
        self,
    ) -> None:
        try:
            chunk_hashes_to_clean = ChunkUsagesService(weaviate_client=self.weaviate_client).get_removable_chunk_hashes(
                last_used_lt=datetime.now().replace(tzinfo=timezone.utc) - self.last_used_at_timedelta,
                chunk_hashes_to_skip=self.exclusion_chunk_hashes,
                chunk_usage_hash_to_skip=[self.usage_hash] if self.usage_hash else [],
            )
            AppLogger.log_debug(f"Cleaning up {len(chunk_hashes_to_clean)} chunks")
            await self._cleanup_chunk_and_chunk_files_objects(chunk_hashes_to_clean=chunk_hashes_to_clean)
        except Exception as _ex:
            AppLogger.log_debug(message=str(_ex))
