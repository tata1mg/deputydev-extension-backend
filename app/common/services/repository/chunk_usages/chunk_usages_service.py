import time
from datetime import datetime, timezone
from typing import List, Tuple

from sanic.log import logger
from weaviate.classes.query import Filter, QueryReference
from weaviate.util import generate_uuid5

from app.common.models.dao.weaviate.chunks_usages import ChunkUsages
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger


class ChunkUsagesService:
    def __init__(self, weaviate_client: WeaviateSyncAndAsyncClients):
        self.weaviate_client = weaviate_client
        self.async_collection = weaviate_client.async_client.collections.get(ChunkUsages.collection_name)
        self.sync_collection = weaviate_client.sync_client.collections.get(ChunkUsages.collection_name)

    def usage_exixts(self, usage_hash: str) -> bool:
        try:
            usage_uuid = generate_uuid5(usage_hash)
            usages = self.sync_collection.query.fetch_objects_by_ids(ids=[usage_uuid], limit=1)
            return len(usages.objects) > 0
        except Exception as ex:
            logger.exception("Failed to check if usage exists")
            raise ex

    def update_last_usage_timestamp(self, usage_hash: str) -> None:
        try:
            usage_uuid = generate_uuid5(usage_hash)
            self.sync_collection.data.update(
                properties={
                    "last_usage_timestamp": datetime.now().replace(tzinfo=timezone.utc),
                },
                uuid=usage_uuid,
            )
        except Exception as ex:
            logger.exception("Failed to update last usage timestamp")
            raise ex

    def add_chunk_usage(self, chunk_hashes: List[str], usage_hash: str, force_create_references: bool = False) -> None:
        try:
            usage_uuid = generate_uuid5(usage_hash)
            time_start = time.perf_counter()
            AppLogger.log_debug(f"Adding chunk usage for {len(chunk_hashes)} chunks in usage {usage_hash}")
            if self.usage_exixts(usage_hash):
                AppLogger.log_debug(f"Usage {usage_hash} already exists")
                self.update_last_usage_timestamp(usage_hash)

            else:
                with self.sync_collection.batch.dynamic() as _batch:
                    _batch.add_object(
                        properties={
                            "last_usage_timestamp": datetime.now().replace(tzinfo=timezone.utc),
                        },
                        uuid=usage_uuid,
                    )

            if not force_create_references:
                return

            with self.sync_collection.batch.dynamic() as _batch:
                for chunk_hash in chunk_hashes:
                    _batch.add_reference(
                        from_property="chunk",
                        from_uuid=usage_uuid,
                        to=generate_uuid5(chunk_hash),
                    )
            AppLogger.log_debug(
                f"Added chunk usage for {len(chunk_hashes)} chunks in usage {usage_hash} in {time.perf_counter() - time_start} seconds"
            )
        except Exception as ex:
            logger.exception("Failed to add chunk usage")
            raise ex

    def get_removable_chunk_hashes_and_usage_ids(
        self, last_used_lt: datetime, chunk_hashes_to_skip: List[str], chunk_usage_hash_to_skip: List[str]
    ) -> Tuple[List[str], List[str]]:
        try:
            AppLogger.log_debug(f"Getting removable chunk usages before {last_used_lt}")
            AppLogger.log_debug(f"Skipping {len(chunk_usage_hash_to_skip)} chunk usages")
            AppLogger.log_debug(f"Skipping {len(chunk_hashes_to_skip)} chunk hashes")
            AppLogger.log_debug(f"chunk_usages_to_skip: {chunk_usage_hash_to_skip}")
            AppLogger.log_debug(
                f"chunk_skip_hash_uuids: {[generate_uuid5(chunk_hash) for chunk_hash in chunk_usage_hash_to_skip]}"
            )

            all_removable_usages = self.sync_collection.query.fetch_objects(
                filters=Filter.all_of(
                    [
                        Filter.by_property("last_usage_timestamp").less_than(last_used_lt),
                        Filter.all_of(
                            [
                                Filter.by_id().not_equal(generate_uuid5(skippable_hash))
                                for skippable_hash in chunk_usage_hash_to_skip
                            ]
                        ),
                    ]
                ),
                limit=10000,
                return_references=QueryReference(
                    link_on="chunk",
                    return_properties=["chunk_hash"],
                ),
            )

            all_removable_chunk_hashes: List[str] = []
            for chunk in all_removable_usages.objects:
                chunk_reference = chunk.references["chunk"] if "chunk" in chunk.references else None
                if not chunk_reference:
                    continue
                for chunk_obj in chunk_reference.objects:
                    if chunk_obj.properties["chunk_hash"] not in chunk_hashes_to_skip:
                        all_removable_chunk_hashes.append(chunk_obj.properties["chunk_hash"])

            return all_removable_chunk_hashes, [str(usage_obj.uuid) for usage_obj in all_removable_usages.objects]

        except Exception as ex:
            logger.exception("Failed to get removable chunk usages")
            raise ex

    def cleanup_old_usages(self, usage_ids: List[str]) -> None:
        batch_size = 500
        for i in range(0, len(usage_ids), batch_size):
            batch = usage_ids[i : i + batch_size]
            self.sync_collection.data.delete_many(Filter.any_of([Filter.by_id().equal(usage_id) for usage_id in batch]))
