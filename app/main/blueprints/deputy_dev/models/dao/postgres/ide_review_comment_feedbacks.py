from enum import Enum
from tortoise import fields
from app.backend_common.models.dao.postgres.base import Base


class IdeReviewCommentFeedbacks(Base):
    serializable_keys = {
        "id",
        "ide_reviews_comment_id",
        "feedback_comment",
        "like",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    ide_reviews_comment_id = fields.BigIntField()
    feedback_comment = fields.TextField(null=True)
    like = fields.BooleanField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "ide_review_comment_feedbacks"
        indexes = (("ide_reviews_comment_id",),)

    class Columns(Enum):
        id = ("id",)
        ide_reviews_comment_id = ("ide_reviews_comment_id",)
        feedback_comment = ("feedback_comment",)
        like = ("like",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)