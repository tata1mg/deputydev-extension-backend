from tortoise import fields

from .base import Base


class FailedOperations(Base):
    serializable_keys = {
        "id",
        "type",
        "data",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    type = fields.TextField()
    data = fields.JSONField()

    class Meta:
        table = "failed_operations"
