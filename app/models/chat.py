import uuid

from pydantic import BaseModel, validator, Field
from typing import Optional, List


class ChatHistoryModel(BaseModel):
    role: str
    prompt: str

    @validator("role")
    def validate_my_field(cls, value):
        allowed_values = {"user", "assistant"}

        if value not in allowed_values:
            raise ValueError(
                f"Invalid value: {value}. The allowed values are {allowed_values}"
            )
        return value


class ChatModel(BaseModel):
    class ChatRequestModel(BaseModel):
        chat_id: Optional[str] = None
        chat_history: Optional[List[ChatHistoryModel]] = None
        current_prompt: str

    class ChatResponseModel(BaseModel):
        chat_id: str = Field(default=str(uuid.uuid4()))
        answer: str
        advice: Optional[str] = None
        followup: Optional[str] = None
