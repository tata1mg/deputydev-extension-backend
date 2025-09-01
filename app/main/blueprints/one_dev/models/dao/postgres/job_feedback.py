from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db import CITextField


class JobFeedback(Base):
    serializable_keys = {
        "id",
        "job_id",
        "feedback",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    job_id = fields.IntField()
    feedback = CITextField(max_length=100)

    class Meta:
        table = "job_feedbacks"
        indexes = (("job_id",),)

    class Columns(Enum):
        id = ("id",)
        job_id = ("job_id",)
        feedback = ("feedback",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
