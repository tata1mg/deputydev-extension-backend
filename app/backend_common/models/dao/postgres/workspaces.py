from enum import Enum

from tortoise import fields

from app.backend_common.utils.tortoise_wrapper.db import CITextField

from .base import Base


class Workspaces(Base):
    serializable_keys = {
        "id",
        "integration_id",
        "name",
        "scm",
        "created_at",
        "updated_at",
        "scm_workspace_id",
        "slug",
        "team_id",
    }

    id = fields.BigIntField(primary_key=True)
    scm_workspace_id = CITextField(max_length=500)
    name = CITextField(max_length=1000)
    scm = fields.CharField(max_length=100)
    integration_id = fields.BigIntField()
    team_id = fields.BigIntField()
    slug = CITextField(max_length=1000)

    class Meta:
        table = "workspaces"
        unique_together = (("scm", "scm_workspace_id"),)  # for a scm scm_workspace_id will always be unique

    class Columns(Enum):
        id = ("id",)
        scm_workspace_id = ("scm_workspace_id",)
        name = ("name",)
        team_id = ("team_id",)
        scm = ("scm",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
        integration_id = ("integration_id",)
        slug = ("slug",)
