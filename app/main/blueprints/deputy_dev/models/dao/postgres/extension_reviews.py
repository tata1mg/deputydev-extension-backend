from enum import Enum
from tortoise import fields
from app.backend_common.models.dao.postgres.base import Base


class ExtensionReviews(Base):
    serializable_keys = {
        "id",
        "user_repo_id",
        "loc",
        "reviewed_files",
        "execution_time_seconds",
        "status",
        "fail_message",
        "review_datetime",
        "is_deleted",
        "deletion_datetime",
        "meta_info",
        "diff_s3_url",
        "created_at",
        "updated_at",
        "ide_reviews_comment_id",
    }

    id = fields.BigIntField(pk=True)
    user_repo_id = fields.BigIntField()
    loc = fields.IntField()
    reviewed_files = fields.JSONField()
    execution_time_seconds = fields.IntField(null=True)
    status = fields.CharField(max_length=20)
    fail_message = fields.TextField(null=True)
    review_datetime = fields.DatetimeField(null=True)
    is_deleted = fields.BooleanField(default=False)
    deletion_datetime = fields.DatetimeField(null=True)
    meta_info = fields.JSONField(null=True)
    diff_s3_url = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "extension_reviews"
        indexes = (("repo_id",),)
        constraints = [
            "FOREIGN KEY (repo_id) REFERENCES repos(id)"
        ]

    class Columns(Enum):
        id = ("id",)
        user_repo_id = ("user_repo_id",)
        loc = ("loc",)
        reviewed_files = ("reviewed_files",)
        execution_time_seconds = ("execution_time_seconds",)
        status = ("status",)
        fail_message = ("fail_message",)
        review_datetime = ("review_datetime",)
        is_deleted = ("is_deleted",)
        deletion_datetime = ("deletion_datetime",)
        meta_info = ("meta_info",)
        diff_s3_key = ("diff_s3_key",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)