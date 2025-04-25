from app.backend_common.models.dao.postgres.base import Base
from tortoise import fields

class ExtensionFeedback(Base):
    serializable_keys = {
        "id",
        "query_id",
        "feedback",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    query_id = fields.IntField()
    feedback = fields.TextField()

    class Meta:
        table = "extension_feedbacks"