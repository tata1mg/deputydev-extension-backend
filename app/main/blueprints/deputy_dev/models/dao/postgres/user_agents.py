from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db import CITextField


class UserAgents(Base):
    serializable_keys = {
        "id",
        "agent_name",
        "user_team_id",
        "display_name",
        "custom_prompt",
        "exclusions",
        "inclusions",
        "confidence_score",
        "objective",
        "is_custom_agent",
        "is_deleted",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(primary_key=True)
    agent_name = CITextField(max_length=1000)
    user_team_id = fields.IntField()
    display_name = fields.CharField(max_length=1000, null=True)
    custom_prompt = fields.TextField(default="")
    exclusions = fields.JSONField(default=list)
    inclusions = fields.JSONField(default=list)
    confidence_score = fields.FloatField(default=0.9)
    objective = fields.TextField(null=True)
    is_custom_agent = fields.BooleanField(default=False)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "user_agents"

    class Columns(Enum):
        id = ("id",)
        agent_name = ("agent_name",)
        user_team_id = ("user_team_id",)
        display_name = ("display_name",)
        custom_prompt = ("custom_prompt",)
        exclusions = ("exclusions",)
        inclusions = ("inclusions",)
        confidence_score = ("confidence_score",)
        objective = ("objective",)
        is_custom_agent = ("is_custom_agent",)
        is_deleted = ("is_deleted",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
