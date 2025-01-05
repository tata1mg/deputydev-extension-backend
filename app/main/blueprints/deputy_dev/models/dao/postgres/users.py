from tortoise import fields

from .......backend_common.models.dao.postgres.base import Base


class Users(Base):
    id = fields.BigIntField(primary_key=True)
    email = fields.CharField(max_length=500)
    name = fields.CharField(max_length=500)
    org_name = fields.CharField(max_length=500)

    class Meta:
        table = "users"
