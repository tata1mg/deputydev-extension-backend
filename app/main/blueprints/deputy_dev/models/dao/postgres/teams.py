from tortoise import fields

from .......backend_common.models.dao.postgres.base import Base


class Teams(Base):
    id = fields.BigIntField(primary_key=True)
    name = fields.CharField(max_length=500)
    llm_model = fields.CharField(max_length=500, null=True)

    class Meta:
        table = "teams"
