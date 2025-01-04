from tortoise import fields

from .......backend_common.models.dao.postgres.base import Base


class Configurations(Base):
    id = fields.BigIntField(primary_key=True)
    configurable_id = fields.BigIntField()
    configurable_type = fields.CharField(max_length=100, null=False)
    configuration = fields.JSONField(null=True)
    error = fields.JSONField(null=True)

    class Meta:
        table = "configurations"
        unique_together = (("configurable_type", "configurable_id"),)
