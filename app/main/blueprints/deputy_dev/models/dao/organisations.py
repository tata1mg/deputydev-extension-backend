from enum import Enum

from tortoise import fields
from tortoise_wrapper.db import CITextField

from .base import Base


class Organisations(Base):
    serializable_keys = {
        "id",
        "name",
        "status",
        "email",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(pk=True)
    name = CITextField(max_length=255, unique=True)
    status = fields.CharField(max_length=100)
    email = fields.CharField(max_length=250)

    class Meta:
        table = "organisations"

    class Columns(Enum):
        id = ("id",)
        name = ("name",)
        status = ("status",)
        email = ("email",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
