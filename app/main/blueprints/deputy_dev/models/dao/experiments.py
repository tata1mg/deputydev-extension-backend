from tortoise import fields
from tortoise_wrapper.db.fields import CITextField, NaiveDatetimeField

from app.main.blueprints.deputy_dev.models.dao.base import Base


class Experiments(Base):
    serializable_keys = {
        "id",
        "scm_pr_id",
        "organisation_id",
        "workspace_id",
        "repo_id",
        "cohort",
        "scm",
        "pr_id",
        "review_status",
        "merge_time_in_sec",
        "human_comment_count",
        "llm_comment_count",
        "scm_creation_time",
        "scm_merge_time",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(pk=True)
    scm_pr_id = CITextField(max_length=100)
    review_status = CITextField(max_length=100)
    organisation_id = fields.BigIntField()
    workspace_id = fields.BigIntField()
    repo_id = fields.BigIntField()
    scm = CITextField(max_length=100)
    pr_id = fields.BigIntField()
    cohort = CITextField(max_length=100)
    merge_time_in_sec = fields.BigIntField(null=True)
    human_comment_count = fields.BigIntField(null=True)
    llm_comment_count = fields.BigIntField(null=True)
    scm_creation_time = NaiveDatetimeField(null=True)
    scm_merge_time = NaiveDatetimeField(null=True)

    class Meta:
        table = "experiments"
