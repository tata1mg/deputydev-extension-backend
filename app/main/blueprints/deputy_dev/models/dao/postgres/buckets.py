from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db.fields import CITextField


class Buckets(Base):
    serializable_keys = {
        "id",
        "name",
        "bucket_type",
        "status",
        "weight",
        "description",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(primary_key=True)
    name = CITextField()
    weight = fields.SmallIntField()
    bucket_type = CITextField(max_length=100)
    status = CITextField(max_length=100)
    is_llm_suggested = fields.BooleanField(default=False)
    description = fields.TextField(null=False)

    class Meta:
        table = "buckets"
        indexes = (("id",),)
        unique_together = (("name",),)

    class Columns(Enum):
        id = ("id",)
        name = ("name",)
        weight = ("weight",)
        bucket_type = ("bucket_type",)
        status = ("status",)
        description = ("description",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
