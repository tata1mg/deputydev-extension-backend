from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class ChatAttachments(Base):
    serializable_keys = {
        "id",
        "s3_key",
        "file_name",
        "file_type",
        "status",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    s3_key = fields.TextField()
    file_name = fields.TextField()
    file_type = fields.TextField()
    status = fields.TextField(null=True)

    class Meta:
        table = "chat_attachments"
