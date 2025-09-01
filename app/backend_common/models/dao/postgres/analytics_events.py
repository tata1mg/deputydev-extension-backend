from tortoise import fields

from app.backend_common.utils.tortoise_wrapper.db import NaiveDatetimeField

from .base import Base


class AnalyticsEvents(Base):
    serializable_keys = {
        "id",
        "event_id",
        "session_id",
        "event_type",
        "event_data",
        "user_team_id",
        "client_version",
        "client",
        "timestamp",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    event_id = fields.UUIDField(null=True)
    session_id = fields.IntField(null=True)
    event_type = fields.TextField()
    event_data = fields.JSONField(null=False)
    client_version = fields.TextField()
    client = fields.TextField()
    user_team_id = fields.IntField(null=False)
    timestamp = NaiveDatetimeField(null=True)

    class Meta:
        table = "analytics_events"
        indexes = (
            ("session_id",),
            ("user_team_id",),
            ("event_type",),
        )
