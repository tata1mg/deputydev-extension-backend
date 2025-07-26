from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class UserAgentCommentMapping(Base):
    serializable_keys = {
        "id",
        "agent_id",
        "comment_id",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(primary_key=True)
    agent = fields.ForeignKeyField("dao.UserAgents", related_name="user_agent_comment_mapping")
    comment = fields.ForeignKeyField("dao.IdeReviewsComments", related_name="user_agent_comment_mapping")

    class Meta:
        table = "user_agent_comment_mapping"
        unique_together = (("agent_id", "comment_id"),)

    class Columns:
        id = "id"
        agent_id = "agent_id"
        comment_id = "comment_id"
        created_at = "created_at"
        updated_at = "updated_at"
