from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db import CITextField


class Job(Base):
    serializable_keys = {
        "id",
        "type",
        "status",
        "session_id",
        "final_output",
        "meta_info",
        "user_team_id",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    type = CITextField(max_length=100)
    status = CITextField(max_length=100)
    session_id = CITextField(max_length=100)
    final_output = fields.JSONField(null=True)
    meta_info = fields.JSONField(null=True)
    user_team_id = fields.IntField(null=False)

    class Meta:
        table = "job"

    class Columns(Enum):
        id = ("id",)
        type = ("type",)
        status = ("status",)
        session_id = ("session_id",)
        final_output = ("final_output",)
        meta_info = ("meta_info",)
        user_team_id = ("user_team_id",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
