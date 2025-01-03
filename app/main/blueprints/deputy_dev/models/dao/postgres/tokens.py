from tortoise import fields

from .......common.models.dao.postgres.base import Base


class Tokens(Base):
    id = fields.BigIntField(primary_key=True)
    token = fields.CharField(max_length=10000)
    type = fields.CharField(
        max_length=500
    )  # refresh / access / workspace_access / installation_id / openai_key / llm_key
    tokenable_type = fields.CharField(max_length=500)  # teams / integrations / workspaces
    tokenable_id = fields.BigIntField()
    expire_at = fields.DatetimeField(null=True)

    class Meta:
        table = "tokens"
