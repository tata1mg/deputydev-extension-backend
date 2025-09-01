from enum import Enum

from tortoise import fields

from app.backend_common.utils.tortoise_wrapper.db import CITextField

from .......backend_common.models.dao.postgres.base import Base


class PRComments(Base):
    serializable_keys = {
        "id",
        "quality_score",
        "iteration",
        "llm_confidence_score",
        "llm_source_model",
        "team_id",
        "scm",
        "workspace_id",
        "repo_id",
        "pr_id",
        "scm_comment_id",
        "scm_author_id",
        "author_name",
        "created_at",
        "updated_at",
        "meta_info",
    }

    id = fields.BigIntField(primary_key=True)
    iteration = fields.IntField()
    llm_confidence_score = fields.FloatField()
    llm_source_model = CITextField(max_length=500)
    team_id = fields.BigIntField()
    scm = CITextField()
    workspace_id = fields.BigIntField()
    repo_id = fields.BigIntField()
    pr_id = fields.BigIntField()
    scm_comment_id = fields.CharField(max_length=100, null=True)
    scm_author_id = fields.CharField(max_length=100)
    author_name = fields.CharField(max_length=1000)
    meta_info = fields.JSONField(null=True)

    class Meta:
        table = "pr_comments"
        unique_together = (("team_id", "scm", "workspace_id", "repo_id", "pr_id", "scm_comment_id"),)
        indexes = (
            (
                "pr_id",
                "created_at",
            ),
            ("repo_id", "created_at"),
            ("workspace_id", "created_at"),
        )

    class Columns(Enum):
        id = ("id",)
        iteration = ("iteration",)
        llm_confidence_score = ("llm_confidence_score",)
        llm_source_model = ("llm_source_model",)
        team_id = ("team_id",)
        scm = ("scm",)
        workspace_id = ("workspace_id",)
        repo_id = ("repo_id",)
        pr_id = ("pr_id",)
        scm_comment_id = ("scm_comment_id",)
        scm_author_id = ("scm_author_id",)
        author_name = ("author_name",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
        meta_info = ("meta_info",)
