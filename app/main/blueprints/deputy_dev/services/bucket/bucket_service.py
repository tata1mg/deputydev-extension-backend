from typing import Dict, List

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.caches.buckets_cache import BucketsCache
from app.main.blueprints.deputy_dev.constants.constants import BucketStatus
from app.main.blueprints.deputy_dev.models.dao.postgres import Buckets
from app.main.blueprints.deputy_dev.models.dto.bucket_dto import BucketDTO


class BucketService:
    BUCKETS_CACHE_KEY = "buckets"
    BUCKET_KEYS = [Buckets.Columns.id.name, Buckets.Columns.description.name, Buckets.Columns.name.name]

    @classmethod
    async def get_published_buckets(cls) -> List[Buckets]:
        # get buckets from cache
        buckets = await BucketsCache.get(cls.BUCKETS_CACHE_KEY)
        if not buckets:
            # get buckets from DB
            buckets = await DB.by_filters(
                Buckets,
                where_clause={"status": BucketStatus.ACTIVE.value},
                order_by=Buckets.Columns.id.name,
                only=cls.BUCKET_KEYS,
            )
            if buckets:
                # cache buckets
                await BucketsCache.set(cls.BUCKETS_CACHE_KEY, buckets)
        return buckets

    @classmethod
    async def get_all_buckets(cls) -> List[Buckets]:
        buckets = await DB.by_filters(Buckets, order_by=Buckets.Columns.id.name, where_clause={})
        return buckets

    @classmethod
    async def db_insert(cls, bucket_dto: BucketDTO) -> Buckets:
        try:
            payload = bucket_dto.dict()
            del payload["id"]
            row = await DB.insert_row(Buckets, payload)
            return row
        except Exception as ex:
            logger.error("not able to insert bucket details {} exception {}".format(bucket_dto.dict(), ex))
            raise ex

    @classmethod
    async def get_all_buckets_dict(cls) -> Dict[str, BucketDTO]:
        # Fetch all buckets
        buckets_data = await BucketService.get_all_buckets()
        # Convert each bucket data to a BucketDTO instance
        buckets = [BucketDTO(**bucket) for bucket in buckets_data]

        # Create a dictionary with the name as the key
        buckets_dict = {bucket.name: bucket for bucket in buckets}

        return buckets_dict
