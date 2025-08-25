from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class QuerySummaries(Base):
    serializable_keys = {
        "id",
        "session_id",
        "query_id",
        "summary",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = fields.IntField(null=False)
    query_id = fields.TextField(null=False)
    summary = fields.TextField(null=False)

    class Meta:
        table = "query_summaries"
        indexes = (("session_id",),)
