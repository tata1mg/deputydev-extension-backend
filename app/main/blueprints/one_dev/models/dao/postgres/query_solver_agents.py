from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class QuerySolverAgent(Base):
    serializable_keys = {
        "id",
        "name",
        "agent_enum",
        "description",
        "prompt_intent",
        "allowed_first_party_tools",
        "status",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    name = fields.TextField()
    agent_enum = fields.TextField()
    description = fields.TextField()
    prompt_intent = fields.TextField()
    status = fields.TextField(default="ACTIVE")
    allowed_first_party_tools = fields.JSONField()

    class Meta:
        table = "query_solver_agents"
        indexes = (("agent_enum",),)
