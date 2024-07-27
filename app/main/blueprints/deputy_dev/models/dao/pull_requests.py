from enum import Enum

from tortoise import fields
from tortoise_wrapper.db import CITextField, NaiveDatetimeField

from .base import Base


class PullRequests(Base):
    serializable_keys = {
        "id",
        "review_status",
        "quality_score",
        "title",
        "description",
        "organisation_id",
        "scm",
        "organisation_id",
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
        "scm_merge_time",
        "commit_id",
    }

    id = fields.BigIntField(pk=True)
    review_status = fields.CharField(max_length=100)
    quality_score = fields.IntField(null=True)
    title = fields.TextField(null=True)
    # organisation_id = fields.ForeignKeyField(
    #     "dao.Organisations",
    #     related_name="pull_requests",
    #     on_update=fields.CASCADE,
    #     source_field="organisation_id",
    #     index=True,
    #     null=False,
    # )
    organisation_id = fields.BigIntField()
    scm = fields.CharField(max_length=100)
    # workspace_id = fields.ForeignKeyField(
    #     "dao.Workspaces",
    #     related_name="pull_requests",
    #     on_update=fields.CASCADE,
    #     source_field="workspace_id",
    #     index=True,
    #     null=False,
    # )
    workspace_id = fields.BigIntField()
    # repo_id = fields.ForeignKeyField(
    #     "dao.Repos",
    #     related_name="pull_requests",
    #     on_update=fields.CASCADE,
    #     source_field="repo_id",
    #     index=True,
    #     null=False,
    # )
    repo_id = fields.BigIntField()
    scm_pr_id = fields.CharField(max_length=100)
    scm_author_id = fields.CharField(max_length=100)
    author_name = fields.CharField(max_length=1000)
    meta_info = fields.JSONField(null=True)
    source_branch = fields.CharField(max_length=1000)
    destination_branch = fields.CharField(max_length=1000)
    scm_creation_time = NaiveDatetimeField(null=True)
    scm_merge_time = NaiveDatetimeField(null=True)
    commit_id = CITextField(max_length=1000)

    class Meta:
        table = "pull_requests"
        unique_together = (("organisation_id", "scm", "workspace_id", "repo_id", "scm_pr_id"),)
        indexes = (
            ("organisation_id", "created_at", "scm"),
            ("repo_id", "created_at"),
            ("workspace_id", "created_at"),
        )

    class Columns(Enum):
        id = ("id",)
        review_status = ("review_status",)
        quality_score = ("quality_score",)
        title = ("title",)
        description = ("description",)
        organisation_id = ("organisation_id",)
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
        scm_merge_time = ("scm_merge_time",)
        commit_id = ("commit_id",)
