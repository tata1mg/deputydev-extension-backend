from enum import Enum

from tortoise import fields

from .base import Base


class MessageSession(Base):
    serializable_keys = {
        "id",
        "summary",
        "user_team_id",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    summary = fields.TextField(null=True)
    client = fields.TextField()
    client_version = fields.TextField(null=True)
    user_team_id = fields.IntField()

    class Meta:
        table = "message_sessions"
        indexes = (("user_team_id",),)
