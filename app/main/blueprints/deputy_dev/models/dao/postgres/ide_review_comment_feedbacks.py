from enum import Enum
from tortoise import fields
from app.backend_common.models.dao.postgres.base import Base


class IdeReviewCommentFeedbacks(Base):
    serializable_keys = {
        "id",
        "comment_id",
        "feedback_comment",
        "like",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    comment = fields.ForeignKeyField(model_name="dao.IdeReviewsComments", related_name="comment_feedback")
    feedback_comment = fields.TextField(null=True)
    like = fields.BooleanField(null=True)

    class Meta:
        table = "ide_review_comment_feedbacks"
        indexes = (("comment_id",),)

    class Columns(Enum):
        id = ("id",)
        comment_id = ("comment_id",)
        feedback_comment = ("feedback_comment",)
        like = ("like",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
