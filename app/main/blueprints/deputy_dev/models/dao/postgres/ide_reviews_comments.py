from enum import Enum
from tortoise import fields
from app.backend_common.models.dao.postgres.base import Base


class IdeReviewsComments(Base):
    serializable_keys = {
        "id",
        "review_id",
        "comment",
        "agent_id",
        "is_deleted",
        "file_path",
        "file_hash",
        "line_number",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    review = fields.ForeignKeyField(model_name="dao.ExtensionReviews", related_name="review_comments")
    comment = fields.TextField()
    agent_id = fields.IntField()
    is_deleted = fields.BooleanField(default=False)
    file_path = fields.TextField()
    file_hash = fields.TextField()
    line_number = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "ide_reviews_comments"
        indexes = (("review_id",),)

    class Columns(Enum):
        id = ("id",)
        review_id = ("review_id",)
        comment = ("comment",)
        agent_id = ("agent_id",)
        is_deleted = ("is_deleted",)
        file_path = ("file_path",)
        file_hash = ("file_hash",)
        line_number = ("line_number",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
