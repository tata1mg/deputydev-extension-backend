from enum import Enum

from tortoise import fields
from tortoise_wrapper.db import CITextField

from .base import Base


class Workspaces(Base):
    serializable_keys = {
        "id",
        "scm_workspace_id",
        "name",
        "organisation_info",
        "scm",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    scm_workspace_id = CITextField(max_length=100)
    name = CITextField(max_length=1000)
    organisation_info = fields.ForeignKeyField(
        "dao.Organisations",
        related_name="workspaces",
        on_update=fields.CASCADE,
        source_field="organisation_id",
        index=True,
        null=False,
    )
    scm = fields.CharField(max_length=100)

    class Meta:
        table = "workspaces"
        unique_together = (("organisation_id", "scm", "scm_workspace_id"),)

    class Columns(Enum):
        id = ("id",)
        scm_workspace_id = ("scm_workspace_id",)
        name = ("name",)
        organisation_id = ("organisation_id",)
        scm = ("scm",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
