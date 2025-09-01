from enum import Enum

from tortoise import fields

from app.backend_common.utils.tortoise_wrapper.db import CITextField, NaiveDatetimeField

from .......backend_common.models.dao.postgres.base import Base


class PullRequests(Base):
    serializable_keys = {
        "id",
        "review_status",
        "quality_score",
        "title",
        "description",
        "team_id",
        "scm",
        "scm",
        "workspace_id",
        "repo_id",
        "scm_pr_id",
        "scm_author_id",
        "author_name",
        "created_at",
        "updated_at",
        "source_branch",
        "destination_branch",
        "scm_creation_time",
        "scm_close_time",
        "commit_id",
        "destination_commit_id",
        "iteration",
        "meta_info",
        "loc_changed",
        "pr_state",
        "scm_approval_time",
        "session_id",
        "session_ids",
    }

    id = fields.BigIntField(primary_key=True)
    review_status = fields.CharField(max_length=100)
    quality_score = fields.IntField(null=True)
    title = fields.TextField(null=True)
    team_id = fields.BigIntField()
    scm = fields.CharField(max_length=100)
    workspace_id = fields.BigIntField()
    repo_id = fields.BigIntField()
    scm_pr_id = fields.CharField(max_length=100)
    scm_author_id = fields.CharField(max_length=100)
    author_name = fields.CharField(max_length=1000)
    meta_info = fields.JSONField(null=True)
    source_branch = fields.CharField(max_length=1000)
    destination_branch = fields.CharField(max_length=1000)
    scm_creation_time = NaiveDatetimeField(null=True)
    scm_close_time = NaiveDatetimeField(null=True)
    commit_id = CITextField(max_length=1000)
    destination_commit_id = CITextField(max_length=1000)
    iteration = fields.BigIntField(null=True)
    loc_changed = fields.BigIntField(null=False)
    pr_state = fields.CharField(max_length=100, null=False)
    scm_approval_time = NaiveDatetimeField(null=True)
    session_id = fields.BigIntField(null=True)
    session_ids = fields.JSONField(null=True)

    class Meta:
        table = "pull_requests"
        unique_together = (
            ("team_id", "scm", "workspace_id", "repo_id", "scm_pr_id", "destination_commit_id", "commit_id"),
        )
        indexes = (
            ("team_id", "created_at", "scm"),
            ("repo_id", "created_at"),
            ("workspace_id", "created_at"),
        )

    class Columns(Enum):
        id = ("id",)
        review_status = ("review_status",)
        quality_score = ("quality_score",)
        title = ("title",)
        description = ("description",)
        team_id = ("team_id",)
        scm = ("scm",)
        workspace_id = ("workspace_id",)
        repo_id = ("repo_id",)
        scm_pr_id = ("scm_pr_id",)
        scm_author_id = ("scm_author_id",)
        author_name = ("author_name",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
        meta_info = ("meta_info",)
        source_branch = ("source_branch",)
        destination_branch = ("destination_branch",)
        scm_creation_time = ("scm_creation_time",)
        scm_close_time = ("scm_close_time",)
        commit_id = ("commit_id",)
        destination_commit_id = ("destination_commit_id",)
        iteration = "iteration"
        loc_changed = ("loc_changed",)
        pr_state = ("pr_state",)
        scm_approval_time = ("scm_approval_time",)
        session_id = ("session_id",)
        session_ids = ("session_ids",)
