from tortoise import fields
from tortoise_wrapper.db import CITextField

from app.backend_common.models.dao.postgres.base import Base


class AgentChats(Base):
    serializable_keys = {
        "id",
        "session_id",
        "actor",
        "message_type",
        "query_id",
        "query_text",
        "attachments",
        "selected_code_snippets",
        "tool_name",
        "tool_use_id",
        "tool_input",
        "metadata",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField(null=False)
    actor = CITextField(max_length=16, null=False)
    message_type = CITextField(max_length=32, null=False)
    query_id = fields.ForeignKeyField("models.AgentChats", null=True, related_name="responses")
    query_text = fields.TextField(null=True)
    attachments = fields.JSONField(null=True)
    selected_code_snippets = fields.JSONField(null=True)
    tool_name = fields.TextField(null=True)
    tool_use_id = fields.TextField(null=True)
    tool_input = fields.JSONField(null=True)
    metadata = fields.JSONField(null=False)

    class Meta:
        table = "chats"
        indexes = (
            ("session_id",),
            ("actor",),
            ("message_type",),
            ("query_id",),
        )
