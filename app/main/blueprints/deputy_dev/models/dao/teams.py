from tortoise import fields

from .base import Base


class Teams(Base):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=500)
    llm_model = fields.CharField(max_length=500, null=True)

    class Meta:
        table = "teams"
