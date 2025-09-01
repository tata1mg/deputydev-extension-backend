from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db.fields import CITextField, NaiveDatetimeField


class Experiments(Base):
    serializable_keys = {
        "id",
        "scm_pr_id",
        "team_id",
        "workspace_id",
        "repo_id",
        "cohort",
        "scm",
        "pr_id",
        "review_status",
        "close_time_in_sec",
        "human_comment_count",
        "llm_comment_count",
        "scm_creation_time",
        "scm_close_time",
        "created_at",
        "updated_at",
        "pr_state",
    }
    id = fields.BigIntField(primary_key=True)
    scm_pr_id = CITextField(max_length=100)
    review_status = CITextField(max_length=100)
    team_id = fields.BigIntField()
    workspace_id = fields.BigIntField()
    repo_id = fields.BigIntField()
    scm = CITextField(max_length=100)
    pr_id = fields.BigIntField()
    cohort = CITextField(max_length=100)
    close_time_in_sec = fields.BigIntField(null=True)
    human_comment_count = fields.BigIntField(null=True)
    llm_comment_count = fields.BigIntField(null=True)
    scm_creation_time = NaiveDatetimeField(null=True)
    scm_close_time = NaiveDatetimeField(null=True)
    pr_state = fields.CharField(max_length=100, null=False)

    class Meta:
        table = "experiments"
