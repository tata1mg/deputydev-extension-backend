from datetime import datetime
from typing import Dict, List

from sanic.log import logger
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5

from app.common.models.dao.weaviate.chunk_files import ChunkFiles
from app.common.models.dto.chunk_file_dto import ChunkFileDTO
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger


class ChunkFilesService:
    def __init__(self, weaviate_client: WeaviateSyncAndAsyncClients):
        self.weaviate_client = weaviate_client
        self.async_collection = weaviate_client.async_client.collections.get(ChunkFiles.collection_name)
        self.sync_collection = weaviate_client.sync_client.collections.get(ChunkFiles.collection_name)

    async def get_chunk_files_by_commit_hashes(self, file_to_commit_hashes: Dict[str, str]) -> List[ChunkFileDTO]:
        BATCH_SIZE = 1000
        MAX_RESULTS_PER_QUERY = 10000
        all_chunk_files = []
        try:
            # Convert dictionary items to list for batch processing
            file_commit_pairs = list(file_to_commit_hashes.items())

            # Process in smaller batches
            for i in range(0, len(file_commit_pairs), BATCH_SIZE):
                batch_pairs = file_commit_pairs[i : i + BATCH_SIZE]

                # Single query per batch without offset pagination
                batch_files = await self.async_collection.query.fetch_objects(
                    filters=Filter.any_of(
                        [
                            Filter.all_of(
                                [
                                    Filter.by_property("file_path").equal(file_path),
                                    Filter.by_property("file_hash").equal(commit_hash),
                                ]
                            )
                            for file_path, commit_hash in batch_pairs
                        ]
                    ),
                    limit=MAX_RESULTS_PER_QUERY,
                )

                # Convert to DTOs efficiently
                if batch_files.objects:
                    batch_dtos = [
                        ChunkFileDTO(
                            **chunk_file_obj.properties,
                            id=str(chunk_file_obj.uuid),
                        )
                        for chunk_file_obj in batch_files.objects
                    ]
                    all_chunk_files.extend(batch_dtos)

            return all_chunk_files

        except Exception as ex:
            logger.exception("Failed to get chunk files by commit hashes")
            raise ex

    async def bulk_insert(self, chunks: List[ChunkFileDTO]) -> None:
        with self.sync_collection.batch.dynamic() as _batch:
            for chunk in chunks:
                chunk_file_uuid = generate_uuid5(
                    f"{chunk.file_path}{chunk.file_hash}{chunk.start_line}{chunk.end_line}"
                )
                _batch.add_object(
                    properties=chunk.model_dump(mode="json", exclude={"id"}),
                    uuid=chunk_file_uuid,
                )

    def cleanup_old_chunk_files(self, last_used_lt: datetime, exclusion_chunk_hashes: List[str]) -> None:
        batch_size = 1000
        while True:
            deletable_objects = self.sync_collection.query.fetch_objects(
                limit=batch_size,
                filters=Filter.all_of(
                    [
                        *[
                            Filter.by_property("chunk_hash").not_equal(chunk_hash)
                            for chunk_hash in exclusion_chunk_hashes
                        ],
                        Filter.by_property("created_at").less_than(last_used_lt),
                    ]
                ),
            )

            AppLogger.log_debug(f"{len(deletable_objects.objects)} chunk_files to be deleted in batch")

            if len(deletable_objects.objects) <= 0:
                break

            result = self.sync_collection.data.delete_many(
                Filter.any_of(
                    [Filter.by_id().equal(obj.uuid) for obj in deletable_objects.objects],
                )
            )
            AppLogger.log_debug(f"chunk_files deleted. successful - {result.successful}, failed - {result.failed}")
