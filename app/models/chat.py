from pydantic import BaseModel, validator, Field
from typing import Optional, List


class ChatHistoryModel(BaseModel):
    role: str
    prompt: str

    @validator('role')
    def validate_my_field(cls, value):
        allowed_values = {'user', 'assistant'}

        if value not in allowed_values:
            raise ValueError(f"Invalid value: {value}. The allowed values are {allowed_values}")
        return value


class ChatRequestModel(BaseModel):
    chat_id: Optional[str] = None
    chat_history: Optional[List[ChatHistoryModel]] = None
    current_prompt: str
