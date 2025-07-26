from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class IdeReviewsComments(Base):
    serializable_keys = {
        "id",
        "title",
        "review_id",
        "comment",
        "corrective_code",
        "rationale",
        "is_deleted",
        "file_path",
        "line_hash",
        "line_number",
        "confidence_score",
        "comment_status",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    review = fields.ForeignKeyField(model_name="dao.IdeReviews", related_name="review_comments")
    title = fields.TextField()
    comment = fields.TextField()
    rationale = fields.TextField(null=True)
    corrective_code = fields.TextField(null=True)
    is_deleted = fields.BooleanField(default=False)
    file_path = fields.TextField()
    line_hash = fields.TextField()
    line_number = fields.IntField()
    tag = fields.CharField(max_length=20, null=True)
    is_valid = fields.BooleanField(default=True)
    confidence_score = fields.FloatField()
    comment_status = fields.TextField(null=True)

    class Meta:
        table = "ide_reviews_comments"
        indexes = (("review_id",),)

    class Columns(Enum):
        id = ("id",)
        title = ("title",)
        review_id = ("review_id",)
        comment = ("comment",)
        rationale = ("rationale",)
        corrective_code = ("corrective_code",)
        is_deleted = ("is_deleted",)
        file_path = ("file_path",)
        line_hash = ("line_hash",)
        line_number = ("line_number",)
        confidence_score = ("confidence_score",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
        comment_status = ("comment_status",)
