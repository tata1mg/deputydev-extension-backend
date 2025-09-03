from enum import Enum

from tortoise import fields

from app.backend_common.utils.tortoise_wrapper.db import CITextField

from .......backend_common.models.dao.postgres.base import Base


class Feedbacks(Base):
    serializable_keys = {
        "id",
        "feedback_type",
        "feedback",
        "pr_id",
        "meta_info",
        "author_info",
        "team_id",
        "workspace_id",
        "scm_pr_id",
        "scm",
        "repo_id",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(primary_key=True)
    feedback_type = CITextField(100)
    feedback = fields.TextField(null=True)
    pr_id = fields.BigIntField(null=True)
    meta_info = fields.JSONField()
    author_info = fields.JSONField()
    team_id = fields.BigIntField()
    workspace_id = fields.BigIntField()
    scm_pr_id = fields.CharField(max_length=100)
    scm = fields.CharField(max_length=100)
    repo_id = fields.BigIntField(null=True)

    class Meta:
        table = "feedbacks"

    class Columns(Enum):
        id = ("id",)
        feedback_type = ("feedback_type",)
        feedback = ("feedback",)
        pr_id = ("created_at",)
        meta_info = ("meta_info",)
        author_info = ("author_info",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
        team_id = ("team_id",)
        workspace_id = ("workspace_id",)
        scm_pr_id = ("scm_pr_id",)
        scm = ("scm",)
        repo_id = ("repo_id",)
