from tortoise import fields

from .base import Base


class Users(Base):
    id = fields.BigIntField(pk=True)
    email = fields.CharField(max_length=500)
    name = fields.CharField(max_length=500)
    org_name = fields.CharField(max_length=500)

    class Meta:
        table = "users"
