from tortoise import fields

from .base import Base


class MessageThread(Base):
    serializable_keys = {
        "id",
        "session_id",
        "actor",
        "query_id",
        "message_type",
        "conversation_chain",
        "message_data",
        "data_hash",
        "usage",
        "llm_model",
        "prompt_type",
        "prompt_category",
        "call_chain_category",
        "metadata",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField()
    actor = fields.TextField()
    query_id = fields.IntField(null=True)
    message_type = fields.TextField()
    conversation_chain = fields.JSONField(null=True)
    message_data = fields.JSONField()
    data_hash = fields.TextField()
    usage = fields.JSONField(null=True)
    llm_model = fields.TextField()
    prompt_type = fields.TextField()
    prompt_category = fields.TextField()
    call_chain_category = fields.TextField()
    metadata = fields.JSONField(null=True)

    class Meta:
        table = "message_threads"
        indexes = (("session_id",),)
