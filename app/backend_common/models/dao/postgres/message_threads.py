from enum import Enum

from tortoise import fields

from .base import Base


class MessageThread(Base):
    serializable_keys = {
        "id",
        "session_id",
        "actor",
        "query_id",
        "type",
        "conversation_chain",
        "data",
        "data_hash",
        "usage",
        "prompt_type",
        "llm_model",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField()
    actor = fields.TextField()
    query_id = fields.IntField()
    type = fields.TextField()
    conversation_chain = fields.JSONField(null=True)
    data = fields.JSONField()
    data_hash = fields.TextField()
    usage = fields.JSONField()
    llm_model = fields.TextField()
    prompt_type = fields.TextField()

    class Meta:
        table = "message_threads"
        indexes = (("session_id",),)

    class Columns(Enum):
        id = ("id",)
        session_id = ("session_id",)
        actor = ("actor",)
        query_id = ("query_id",)
        type = ("type",)
        conversation_chain = ("conversation_chain",)
        data = ("data",)
        data_hash = ("data_hash",)
        usage = ("usage",)
        prompt_type = ("prompt_type",)
        llm_model = ("llm_model",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
