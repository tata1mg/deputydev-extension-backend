from enum import Enum
from tortoise import fields
from app.backend_common.models.dao.postgres.base import Base


class IdeReviewFeedback(Base):
    serializable_keys = {
        "id",
        "review_id",
        "feedback_comment",
        "like",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    review = fields.ForeignKeyField(model_name="dao.IdeReviews", related_name="review_feedback")
    feedback_comment = fields.TextField(null=True)
    like = fields.BooleanField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "extension_reviews_feedbacks"
        indexes = (("review_id",),)

    class Columns(Enum):
        id = ("id",)
        review_id = ("review_id",)
        feedback_comment = ("feedback_comment",)
        like = ("like",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
