from tortoise import fields
from .base import Base
import uuid


class Agents(Base):
    id = fields.BigIntField(pk=True)
    agent_id = fields.CharField(max_length=36, null=False)
    repo_id = fields.BigIntField(null=False)
    display_name = fields.CharField(max_length=100, null=False)
    agent_name = fields.CharField(max_length=100, null=False)

    class Meta:
        table = "agents"
        unique_together = (("repo_id", "agent_id"),)
