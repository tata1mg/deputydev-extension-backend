from tortoise import fields

from .base import Base


class FailedKafkaMessages(Base):
    serializable_keys = {
        "id",
        "message_data",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    message_data = fields.JSONField()

    class Meta:
        table = "failed_kafka_messages"
