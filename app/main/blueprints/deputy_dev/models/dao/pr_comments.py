from enum import Enum

from tortoise import fields
from tortoise_wrapper.db import CITextField

from .base import Base


class PRComments(Base):
    serializable_keys = {
        "id",
        "quality_score",
        "bucket_id",
        "iteration",
        "llm_confidence_score",
        "llm_source_model",
        "organisation_id",
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

    id = fields.BigIntField(pk=True)
    # bucket_id = fields.ForeignKeyField(
    #     "dao.Buckets",
    #     related_name="pr_components",
    #     on_update=fields.CASCADE,
    #     source_field="bucket_id",
    #     index=True,
    #     null=False,
    # )
    bucket_id = fields.SmallIntField()
    iteration = fields.IntField()
    llm_confidence_score = fields.FloatField()
    llm_source_model = CITextField(max_length=500)
    # organisation_id = fields.ForeignKeyField(
    #     "dao.Organisations",
    #     related_name="pr_components",
    #     on_update=fields.CASCADE,
    #     source_field="organisation_id",
    #     index=True,
    #     null=False,
    # )
    organisation_id = fields.BigIntField()
    scm = CITextField()
    # workspace_id = fields.ForeignKeyField(
    #     "dao.Workspaces",
    #     related_name="pr_components",
    #     on_update=fields.CASCADE,
    #     source_field="workspace_id",
    #     index=True,
    #     null=False,
    # )
    workspace_id = fields.BigIntField()
    # repo_id = fields.ForeignKeyField(
    #     "dao.Repos",
    #     related_name="pr_components",
    #     on_update=fields.CASCADE,
    #     source_field="repo_id",
    #     index=True,
    #     null=False,
    # )
    repo_id = fields.BigIntField()
    # pr_id = fields.ForeignKeyField(
    #     "dao.PullRequests",
    #     related_name="pr_components",
    #     on_update=fields.CASCADE,
    #     source_field="pr_id",
    #     index=True,
    #     null=False,
    # )
    pr_id = fields.BigIntField()
    scm_comment_id = fields.CharField(max_length=100)
    scm_author_id = fields.CharField(max_length=100)
    author_name = fields.CharField(max_length=1000)
    meta_info = fields.JSONField(null=True)

    class Meta:
        table = "pr_comments"
        unique_together = (("organisation_id", "scm", "workspace_id", "repo_id", "pr_id", "scm_comment_id"),)
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
        bucket_id = ("bucket_id",)
        iteration = ("iteration",)
        llm_confidence_score = ("llm_confidence_score",)
        llm_source_model = ("llm_source_model",)
        organisation_id = ("organisation_id",)
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
