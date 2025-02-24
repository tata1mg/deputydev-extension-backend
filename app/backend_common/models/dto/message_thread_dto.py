from ast import Dict
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class MessageThreadActor(Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class MessageType(Enum):
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    TOOL_RESPONSE = "TOOL_RESPONSE"


class MessageDataTypes(Enum):
    TEXT = "TEXT"
    TOOL_USE_REQUEST = "TOOL_USE_REQUEST"
    TOOL_USE_RESPONSE = "TOOL_USE_RESPONSE"


class UserQueryMessageData(BaseModel):
    type: Literal[MessageDataTypes.TEXT] = MessageDataTypes.TEXT
    text: str


class ToolUseRequestMessageData(BaseModel):
    type: Literal[MessageDataTypes.TOOL_USE_REQUEST] = MessageDataTypes.TOOL_USE_REQUEST
    tool_name: str
    tool_use_id: str
    input_params_json: Dict[str, Any]


class ToolUseResponseMessageData(BaseModel):
    type: Literal[MessageDataTypes.TOOL_USE_RESPONSE] = MessageDataTypes.TOOL_USE_RESPONSE
    tool_name: str
    tool_use_id: str
    response: Dict[str, Any]


MessageData = Annotated[
    Union[UserQueryMessageData, ToolUseRequestMessageData, ToolUseResponseMessageData], Field(discriminator="type")
]


class LLModels(Enum):
    GPT_4O = "GPT_4O"
    CLAUDE_3_POINT_5_SONNET = "CLAUDE_3_POINT_5_SONNET"
    GPT_40_MINI = "GPT_40_MINI"
    GPT_O1_MINI = "GPT_O1_MINI"


class LLMUsage(BaseModel):
    input: int
    output: int
    cache_read: Optional[int] = None
    cache_write: Optional[int] = None

    def __add__(self, other: "LLMUsage") -> "LLMUsage":
        return LLMUsage(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_read=(self.cache_read or 0) + (other.cache_read or 0)
            if self.cache_read is not None or other.cache_read is not None
            else None,
            cache_write=(self.cache_write or 0) + (other.cache_write or 0)
            if self.cache_write is not None or other.cache_write is not None
            else None,
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MessageThreadData(BaseModel):
    session_id: str
    actor: MessageThreadActor
    query_id: List[int] = []
    message_type: MessageType
    previous_context_message_ids: List[int] = []
    message_data: List[MessageData]
    llm_model: LLModels
    usage: LLMUsage


class MessageThreadDTO(MessageThreadData):
    id: int
    created_at: datetime
    updated_at: datetime
