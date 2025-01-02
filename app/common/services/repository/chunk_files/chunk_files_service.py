from typing import Dict, List

from sanic.log import logger
from weaviate import WeaviateAsyncClient
from weaviate.classes.query import Filter
from weaviate.collections.classes.data import DataObject

from app.common.models.dao.weaviate.chunk_files import ChunkFiles
from app.common.models.dto.chunk_file_dto import ChunkFileDTO


class ChunkFilesService:
    def __init__(self, weaviate_client: WeaviateAsyncClient):
        self.weaviate_client = weaviate_client
        self.collection = weaviate_client.collections.get(ChunkFiles.collection_name)

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
                batch_files = await self.collection.query.fetch_objects(
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
        await self.collection.data.insert_many(
            [DataObject(properties=chunk.model_dump(mode="json", exclude={"id"})) for chunk in chunks]
        )
