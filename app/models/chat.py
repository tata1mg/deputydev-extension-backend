import uuid

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Any

from pydantic.v1 import root_validator


class ChatHistoryModel(BaseModel):
    role: str
    type: str
    prompt: str

    @field_validator("role")
    def validate_role(cls, value):
        allowed_values = {"user", "assistant"}
        if value not in allowed_values:
            raise ValueError(
                f"Invalid value: {value}. The allowed values are {allowed_values}"
            )
        return value

    @field_validator("type")
    def validate_type(cls, value):
        allowed_values = {
            ChatTypeMsg.__name__,
            ChatTypeSkuCard.__name__,
            ChatTypeCallAgent.__name__,
            "ChatTypePdf"
        }
        if value not in allowed_values:
            raise ValueError(
                f"Invalid value: {value}. The allowed values are {allowed_values}"
            )
        return value


class ChatTypeMsg(BaseModel):
    type: str = "ChatTypeMsg"
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
    type: str = "ChatTypeSkuCard"
    header: str
    sub_header: Optional[str] = None
    eta: Optional[Any] = None
    price: Optional[Any] = None
    sku_id: str
    cta: Any
    slug_url: str
    sku_image: str
    sku_type: str
    target_url: str


class ChatTypeCallAgent(BaseModel):
    type: str = "ChatTypeCallAgent"
    icon: str = "https://onemg.gumlet.io/574fdd07-582a-4052-a4f1-7a3a0b5a19b1.webp"
    header: str = "Call our health advisor to book"
    sub_header: str = "Our team of experts will guide you"
    target_url: str = "tel://01206025703"


class ChatModel(BaseModel):
    class ChatRequestModel(BaseModel):
        chat_id: Optional[str] = None
        chat_history: Optional[List[ChatHistoryModel]] = None
        current_prompt: Optional[str] = None
        chat_type: Optional[str] = None
        file_url: Optional[str] = None

        # @root_validator
        # def validate(cls, values):
        #     if not values.get("current_prompt") or not values.get("name"):
        #         raise ValueError("It's an error")
        #     return values

    class ChatResponseModel(BaseModel):
        chat_id: str = Field(default=str(uuid.uuid4()))
        data: List[Union[ChatTypeMsg, ChatTypeSkuCard, ChatTypeCallAgent, None]]
