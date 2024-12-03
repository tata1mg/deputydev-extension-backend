from enum import Enum

from tortoise import fields
from tortoise_wrapper.db import CITextField

from .base import Base


class Repos(Base):
    serializable_keys = {
        "id",
        "name",
        "team_id",
        "scm",
        "workspace_id",
        "scm_repo_id",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(pk=True)
    name = CITextField(max_length=1000)
    team_id = fields.BigIntField()
    scm = fields.CharField(max_length=1000)
    workspace_id = fields.BigIntField()
    scm_repo_id = fields.CharField(max_length=100)

    class Meta:
        table = "repos"
        unique_together = (("workspace_id", "scm_repo_id"),)  # workspace have team_id and scm
        indexes = (("workspace_id",),)

    class Columns(Enum):
        id = ("id",)
        name = ("name",)
        team_id = ("team_id",)
        scm = ("scm",)
        workspace_id = ("workspace_id",)
        scm_repo_id = ("scm_repo_id",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
