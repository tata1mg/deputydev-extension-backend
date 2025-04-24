from tortoise import fields
from tortoise.models import Model
from app.backend_common.models.dao.postgres.base import Base


class Url(Base):
    serializable_keys = {
        "id",
        "name",
        "url",
        "user_team_id",
        "is_deleted",
        "created_at",
        "updated_at",
    }
    id = fields.IntField(primary_key=True)
    name = fields.TextField()
    url = fields.TextField()
    user_team_id = fields.IntField()
    is_deleted = fields.BooleanField(default=False)
    last_indexed = fields.DatetimeField(null=True)

    class Meta:
        table = "urls"
