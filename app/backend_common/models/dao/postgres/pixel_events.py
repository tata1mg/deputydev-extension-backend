from tortoise import fields
from tortoise_wrapper.db import NaiveDatetimeField

from .base import Base


class PixelEvents(Base):
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
        "client",
        "timestamp",
        "source",
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
    source = fields.TextField(null=True)
    client_version = fields.TextField()
    client = fields.TextField()
    timestamp = NaiveDatetimeField(null=True)

    class Meta:
        table = "pixel_events"
        indexes = (("session_id",), ("user_id",), ("team_id",))
