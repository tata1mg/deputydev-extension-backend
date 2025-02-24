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
        "previous_query_ids",
        "data",
        "usage",
        "llm_model",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField()
    actor = fields.TextField()
    query_id = fields.IntField()
    type = fields.TextField()
    previous_query_ids = fields.JSONField()
    data = fields.JSONField()
    usage = fields.JSONField()
    llm_model = fields.TextField()

    class Meta:
        table = "message_threads"
        indexes = (("session_id",),)

    class Columns(Enum):
        id = ("id",)
        session_id = ("session_id",)
        actor = ("actor",)
        query_id = ("query_id",)
        type = ("type",)
        previous_query_ids = ("previous_query_ids",)
        data = ("data",)
        usage = ("usage",)
        llm_model = ("llm_model",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
