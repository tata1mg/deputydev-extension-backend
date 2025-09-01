from tortoise import fields

from app.backend_common.utils.tortoise_wrapper.db import NaiveDatetimeField

from .base import Base


class ErrorAnalyticsEvents(Base):
    serializable_keys = {
        "id",
        "error_id",
        "user_email",
        "error_type",
        "error_data",
        "repo_name",
        "error_source",
        "client_version",
        "timestamp",
        "stack_trace",
        "user_team_id",
        "session_id",
        "user_system_info",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    error_id = fields.UUIDField(null=True)
    user_email = fields.TextField(null=True)
    error_type = fields.TextField()
    error_data = fields.JSONField(null=False)
    repo_name = fields.TextField(null=True)
    error_source = fields.TextField()
    client_version = fields.TextField()
    timestamp = NaiveDatetimeField(null=False)
    user_team_id = fields.BigIntField(null=True)
    session_id = fields.BigIntField(null=True)
    stack_trace = fields.TextField(null=True)
    user_system_info = fields.JSONField(null=True)

    class Meta:
        table = "error_analytics_events"
        indexes = (
            ("timestamp",),
            ("user_email", "timestamp"),
        )
