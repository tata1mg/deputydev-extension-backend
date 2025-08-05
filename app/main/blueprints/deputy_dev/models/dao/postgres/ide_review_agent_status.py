from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class IdeReviewAgentStatus(Base):
    serializable_keys = {
        "id",
        "review_id",
        "agent_id",
        "meta_info",
        "llm_model",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    review = fields.ForeignKeyField(model_name="dao.IdeReviews", related_name="agent_status")
    agent = fields.ForeignKeyField(model_name="dao.UserAgents", related_name="review_status")
    meta_info = fields.JSONField(null=True)
    llm_model = fields.TextField(null=True)

    class Meta:
        table = "review_agent_status"
        indexes = (
            ("review_id",),
            ("agent_id",),
        )

    class Columns(Enum):
        id = ("id",)
        review_id = ("review_id",)
        agent_id = ("agent_id",)
        meta_info = ("meta_info",)
        llm_model = ("llm_model",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
