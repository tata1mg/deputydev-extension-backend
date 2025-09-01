from enum import Enum

from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base
from app.backend_common.utils.tortoise_wrapper.db import CITextField


class SessionChats(Base):
    serializable_keys = {
        "id",
        "session_id",
        "prompt_type",
        "llm_prompt",
        "llm_response",
        "llm_model",
        "user_query",
        "response_summary",
        "code_lines_count",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    session_id = CITextField(max_length=100)
    prompt_type = CITextField(max_length=100)
    llm_prompt = CITextField(max_length=1000000)
    llm_response = CITextField(max_length=1000000)
    llm_model = CITextField(max_length=100)
    response_summary = CITextField(max_length=1000000)
    user_query = CITextField(max_length=1000000)
    code_lines_count = fields.BigIntField(null=True)

    class Meta:
        table = "session_chats"
        indexes = (("session_id",),)

    class Columns(Enum):
        id = ("id",)
        session_id = ("session_id",)
        prompt_type = ("prompt_type",)
        llm_prompt = ("llm_prompt",)
        llm_response = ("llm_response",)
        llm_model = ("llm_model",)
        response_summary = ("response_summary",)
        user_query = ("user_query",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
