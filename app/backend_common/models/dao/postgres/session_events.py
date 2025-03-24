from tortoise import fields
from tortoise_wrapper.db import NaiveDatetimeField

from .base import Base


class SessionEvents(Base):
    serializable_keys = {
        "id",
        "event_id",
        "session_id",
        "event_type",
        "lines",
        "file_path",
        "user_id",
        "team_id",
        "client_version",
        "timestamp",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    event_id = fields.UUIDField()
    session_id = fields.IntField()
    event_type = fields.TextField()
    lines = fields.IntField()
    file_path = fields.TextField(null=True)
    user_id = fields.IntField()
    team_id = fields.IntField()
    client_version = fields.IntField()
    timestamp = NaiveDatetimeField(null=True)

    class Meta:
        table = "session_events"
        indexes = (("session_id",), ("user_id",), ("team_id",))