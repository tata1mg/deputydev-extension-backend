from app.common.services.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.comment_bucket_mapping import (
    CommentBucketMapping,
)


class CommentBucketMappingService:
    @classmethod
    async def bulk_insert(cls, mappings: list[CommentBucketMapping]):
        rows_inserted = await DB.bulk_create(CommentBucketMapping, mappings)
        return rows_inserted
