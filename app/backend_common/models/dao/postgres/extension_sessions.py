from tortoise import fields

from .base import Base


class ExtensionSession(Base):
    serializable_keys = {
        "id",
        "session_id",
        "user_team_id",
        "summary",
        "pinned_rank",
        "status",
        "session_type",
        "current_model",
        "created_at",
        "updated_at",
        "deleted_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField()
    user_team_id = fields.IntField()
    summary = fields.TextField(null=True)
    pinned_rank = fields.IntField(null=True)
    status = fields.TextField(null=False, default="ACTIVE")
    session_type = fields.TextField(null=False)
    deleted_at = fields.DatetimeField(null=True)
    current_model = fields.TextField(null=True)

    class Meta:
        table = "extension_sessions"
        indexes = (
            ("session_id",),
            ("user_team_id",),
        )
