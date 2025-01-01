from enum import Enum

from tortoise import fields
from tortoise_wrapper.db import CITextField

from app.common.models.dao.postgres.base import Base


class Job(Base):
    serializable_keys = {
        "id",
        "type",
        "status",
        "session_id",
        "final_output",
        "meta_info",
        "team_id",
        "advocacy_id",
        "user_email",
        "user_name",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    type = CITextField(max_length=100)
    status = CITextField(max_length=100)
    session_id = CITextField(max_length=100)
    final_output = fields.JSONField(null=True)
    meta_info = fields.JSONField(null=True)
    team_id = fields.IntField(null=False)
    advocacy_id = fields.IntField(null=False)
    user_email = CITextField(max_length=100, null=True)
    user_name = CITextField(max_length=100, null=True)

    class Meta:
        table = "job"

    class Columns(Enum):
        id = ("id",)
        type = ("type",)
        status = ("status",)
        session_id = ("session_id",)
        final_output = ("final_output",)
        meta_info = ("meta_info",)
        team_id = ("team_id",)
        advocacy_id = ("advocacy_id",)
        user_email = ("user_email",)
        user_name = ("user_name",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
