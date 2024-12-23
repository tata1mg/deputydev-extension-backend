from app.main.blueprints.deputy_dev.models.dao.comment_bucket_mapping import (
    CommentBucketMapping,
)
from app.main.blueprints.deputy_dev.services.db.db import DB


class CommentBucketMappingService:
    @classmethod
    async def bulk_insert(cls, mappings: list[CommentBucketMapping]):
        rows_inserted = await DB.bulk_create(CommentBucketMapping, mappings)
        return rows_inserted
