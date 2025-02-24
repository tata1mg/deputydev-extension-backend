from enum import Enum

from tortoise import fields

from .base import Base


class MessageSessions(Base):
    serializable_keys = {
        "id",
        "summary",
        "user_team_id",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    summary = fields.TextField()
    user_team_id = fields.IntField()

    class Meta:
        table = "message_sessions"
        indexes = (("session_id",),)

    class Columns(Enum):
        id = ("id",)
        summary = ("summary",)
        user_team_id = ("user_team_id",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
