from enum import Enum

from tortoise import fields

from ...constants.constants import SCMType
from .base import Base


class OrgScmAccounts(Base):
    serializable_keys = {
        "id",
        "organisation_id",
        "scm",
        "token",
        "scm_account_id",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    organisation_id = fields.ForeignKeyField(
        "dao.Organisations",
        related_name="org_scm_accounts",
        on_update=fields.CASCADE,
        source_field="organisation_id",
        index=True,
        null=False,
    )
    scm = fields.CharEnumField(SCMType)
    token = fields.CharField(max_length=500, null=True)
    scm_account_id = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "org_scm_accounts"
        unique_together = (("organisation_id", "scm"),)

    class Columns(Enum):
        id = ("id",)
        organisation_id = ("organisation_id",)
        scm = ("scm",)
        token = ("token",)
        scm_account_id = ("scm_account_id",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
