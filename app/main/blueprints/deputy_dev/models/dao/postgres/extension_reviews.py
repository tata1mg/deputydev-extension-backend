from enum import Enum
from tortoise import fields
from app.backend_common.models.dao.postgres.base import Base


class ExtensionReviews(Base):
    serializable_keys = {
        "id",
        "review_status",
        "user_team_id",
        "repo_id",
        "loc",
        "reviewed_files",
        "execution_time_seconds",
        "source_branch",
        "target_branch",
        "source_commit",
        "target_commit",
        "fail_message",
        "review_datetime",
        "is_deleted",
        "deletion_datetime",
        "meta_info",
        "session_id"
        "diff_s3_url",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    review_status = fields.CharField(max_length=100)
    user_team = fields.ForeignKeyField(model_name="dao.UserTeams", related_name="review_user_team")
    repo = fields.ForeignKeyField(model_name="dao.Repos", related_name="review_repo")
    # user_team = fields.ForeignKeyField(model_name="dao.UserTeams", related_name="review_user_team")
    loc = fields.IntField()
    reviewed_files = fields.JSONField()
    execution_time_seconds = fields.IntField(null=True)
    source_branch = fields.TextField(null=True)
    target_branch = fields.TextField(null=True)
    source_commit = fields.TextField(null=True)
    target_commit = fields.TextField(null=True)
    fail_message = fields.TextField(null=True)
    review_datetime = fields.DatetimeField(null=True)
    is_deleted = fields.BooleanField(default=False)
    deletion_datetime = fields.DatetimeField(null=True)
    meta_info = fields.JSONField(null=True)
    diff_s3_url = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    session_id = fields.BigIntField(null=True)

    class Meta:
        table = "extension_reviews"
        indexes = (("repo_id",),)
        constraints = ["FOREIGN KEY (repo_id) REFERENCES repos(id)"]

    class Columns(Enum):
        id = ("id",)
        review_status = ("review_status",)
        user_team_id = ("user_team_id",)
        repo_id = ("repo_id",)
        loc = ("loc",)
        reviewed_files = ("reviewed_files",)
        execution_time_seconds = ("execution_time_seconds",)
        fail_message = ("fail_message",)
        review_datetime = ("review_datetime",)
        is_deleted = ("is_deleted",)
        deletion_datetime = ("deletion_datetime",)
        meta_info = ("meta_info",)
        diff_s3_key = ("diff_s3_key",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
        source_branch = ("source_branch",)
        target_branch = ("target_branch",)
        source_commit = ("source_commit",)
        target_commit = ("target_commit",)
        session_id = ("session_id",)
