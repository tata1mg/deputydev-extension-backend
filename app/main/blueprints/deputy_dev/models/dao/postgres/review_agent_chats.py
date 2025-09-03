from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db import CITextField


class ReviewAgentChats(Base):
    serializable_keys = {
        "id",
        "session_id",
        "agent_id",
        "actor",
        "message_type",
        "message_data",
        "metadata",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField(null=False)
    agent_id = fields.TextField(null=False)
    actor = CITextField(max_length=16, null=False)
    message_type = CITextField(max_length=16, null=False)
    message_data = fields.JSONField(null=False)
    metadata = fields.JSONField(null=False)

    class Meta:
        table = "review_agent_chats"
        indexes = (
            ("session_id",),
            ("actor",),
            ("message_type",),
        )

    class Columns(Enum):
        id = ("id",)
        session_id = ("session_id",)
        agent_id = ("agent_id",)
        actor = ("actor",)
        message_type = ("message_type",)
        message_data = ("message_data",)
        metadata = ("metadata",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
