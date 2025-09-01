from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db import NaiveDatetimeField


class Url(Base):
    serializable_keys = {"id", "name", "url", "user_team_id", "is_deleted", "created_at", "updated_at", "last_indexed"}
    id = fields.IntField(primary_key=True)
    name = fields.TextField()
    url = fields.TextField()
    user_team_id = fields.IntField()
    is_deleted = fields.BooleanField(default=False)
    last_indexed = NaiveDatetimeField(null=True)

    class Meta:
        table = "urls"
