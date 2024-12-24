from tortoise import fields

from .base import Base


class AgentCommentMappings(Base):
    serializable_keys = {
        "id",
        "pr_comment_id",
        "agent_id",
        "weight"
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    pr_comment_id = fields.ForeignKeyField("dao.PRComments")
    agent_id = fields.ForeignKeyField("dao.Agents")
    weight = fields.FloatField()

    class Meta:
        table = "agent_comment_mappings"
        unique_together = (("pr_comment_id", "agent_id"),)
