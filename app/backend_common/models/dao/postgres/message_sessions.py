from tortoise import fields

from .base import Base


class MessageSession(Base):
    serializable_keys = {
        "id",
        "summary",
        "client",
        "client_version",
        "user_team_id",
        "status",
        "created_at",
        "updated_at",
        "deleted_at",
    }

    id = fields.IntField(primary_key=True)
    summary = fields.TextField(null=True)
    client = fields.TextField()
    client_version = fields.TextField(null=True)
    user_team_id = fields.IntField()
    status = fields.TextField()
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "message_sessions"
        indexes = (("user_team_id",),)
