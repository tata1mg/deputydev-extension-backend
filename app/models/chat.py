import uuid

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union


class ChatHistoryModel(BaseModel):
    role: str
    type: Optional[str] = None
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
    type: str = "message"
    answer: str
    advice: Optional[str] = None


class Image(BaseModel):
    url: str
    alt: str


class Eta(BaseModel):
    label: str
    image: Image


class Details(BaseModel):
    target_url: str


class Cta(BaseModel):
    action: str
    text: str
    details: Details


class Price(BaseModel):
    mrp: Optional[str]
    discount: Optional[str]
    discounted_price: Optional[str]
    price_suffix: Optional[str]


class ChatTypeSkuCard(BaseModel):
    header: str
    sub_header: Optional[str] = None
    eta: Eta
    price: Price
    sku_id: str
    cta: Cta
    slug_url: str


class ChatModel(BaseModel):
    class ChatRequestModel(BaseModel):
        chat_id: Optional[str] = None
        chat_history: Optional[List[ChatHistoryModel]] = None
        current_prompt: Optional[str] = None

    class ChatResponseModel(BaseModel):
        chat_id: str = Field(default=str(uuid.uuid4()))
        data: List[Union[ChatTypeMsg, ChatTypeSkuCard, None]]
