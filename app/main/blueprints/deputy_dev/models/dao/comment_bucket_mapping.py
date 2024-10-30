from tortoise import fields

from .base import Base


class CommentBucketMapping(Base):
    serializable_keys = {
        "id",
        "pr_comment_id",
        "bucket_id",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    pr_comment_id = fields.BigIntField()
    bucket_id = fields.BigIntField()

    class Meta:
        table = "comment_bucket_mapping"
        unique_together = (("pr_comment_id", "bucket_id"),)
