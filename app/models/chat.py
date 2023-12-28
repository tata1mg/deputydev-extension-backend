import uuid

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union


class ChatHistoryModel(BaseModel):
    role: str
    type:  Optional[str] = None
    prompt: str

    @field_validator("role")
    def validate_my_field(cls, value):
        allowed_values = {"user", "assistant"}

        if value not in allowed_values:
            raise ValueError(
                f"Invalid value: {value}. The allowed values are {allowed_values}"
            )
        return value


class ChatTypeMsg(BaseModel):
    type:  str = "message"
    answer: str
    advice: Optional[str] = None


class ChatTypeSkuCard(BaseModel):
    header: str
    sub_header: str
    report_eta: str
    icon: str
    price: str
    sku_id: str
    target_url: str
    cta: str


class ChatModel(BaseModel):
    class ChatRequestModel(BaseModel):
        chat_id: Optional[str] = None
        chat_history: Optional[List[ChatHistoryModel]] = None
        current_prompt: Optional[str] = None

    class ChatResponseModel(BaseModel):
        chat_id: str = Field(default=str(uuid.uuid4()))
        data: List[Union[ChatTypeMsg, ChatTypeSkuCard, None]]
