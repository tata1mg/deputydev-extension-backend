from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Sequence, Union

from pydantic import BaseModel, ConfigDict, Field


class MessageThreadActor(Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class MessageType(Enum):
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    TOOL_RESPONSE = "TOOL_RESPONSE"


class ContentBlockCategory(str, Enum):
    TEXT_BLOCK = "TEXT_BLOCK"
    TOOL_USE_REQUEST = "TOOL_USE_REQUEST"
    TOOL_USE_RESPONSE = "TOOL_USE_RESPONSE"
    FILE = "FILE"


class TextBlockContent(BaseModel):
    text: str

class FileContent(BaseModel):
    file_type: str
    s3_key: str

class ToolUseRequestContent(BaseModel):
    tool_input: Dict[str, Any]
    tool_name: str
    tool_use_id: str


class ToolUseResponseContent(BaseModel):
    tool_name: str
    tool_use_id: str
    response: Union[str, Dict[str, Any]]


class TextBlockData(BaseModel):
    type: Literal[ContentBlockCategory.TEXT_BLOCK] = ContentBlockCategory.TEXT_BLOCK
    content: TextBlockContent
    content_vars: Optional[Dict[str, Any]] = None

class FileBlockData(BaseModel):
    type: Literal[ContentBlockCategory.FILE] = ContentBlockCategory.FILE
    content: List[FileContent]

class ToolUseRequestData(BaseModel):
    type: Literal[ContentBlockCategory.TOOL_USE_REQUEST] = ContentBlockCategory.TOOL_USE_REQUEST
    content: ToolUseRequestContent


class ToolUseResponseData(BaseModel):
    type: Literal[ContentBlockCategory.TOOL_USE_RESPONSE] = ContentBlockCategory.TOOL_USE_RESPONSE
    content: ToolUseResponseContent


ResponseData = Annotated[Union[TextBlockData, FileBlockData, ToolUseRequestData], Field(discriminator="type")]

MessageData = Annotated[Union[ResponseData, ToolUseResponseData], Field(discriminator="type")]


class LLModels(Enum):
    GPT_4O = "GPT_4O"
    CLAUDE_3_POINT_5_SONNET = "CLAUDE_3_POINT_5_SONNET"
    CLAUDE_3_POINT_7_SONNET = "CLAUDE_3_POINT_7_SONNET"
    GPT_40_MINI = "GPT_40_MINI"
    GPT_O1_MINI = "GPT_O1_MINI"
    GEMINI_2_POINT_5_PRO = "GEMINI_2_POINT_5_PRO"
    GEMINI_2_POINT_0_FLASH = "GEMINI_2_POINT_0_FLASH"
    GPT_4_POINT_1 = "GPT_4_POINT_1"


class LLMUsage(BaseModel):
    input: int
    output: int
    cache_read: Optional[int] = None
    cache_write: Optional[int] = None

    def __add__(self, other: "LLMUsage") -> "LLMUsage":
        return LLMUsage(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_read=(
                (self.cache_read or 0) + (other.cache_read or 0)
                if self.cache_read is not None or other.cache_read is not None
                else None
            ),
            cache_write=(
                (self.cache_write or 0) + (other.cache_write or 0)
                if self.cache_write is not None or other.cache_write is not None
                else None
            ),
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MessageCallChainCategory(Enum):
    CLIENT_CHAIN = "CLIENT_CHAIN"
    SYSTEM_CHAIN = "SYSTEM_CHAIN"


class MessageThreadData(BaseModel):
    session_id: int
    actor: MessageThreadActor
    query_id: Optional[int] = None
    message_type: MessageType
    conversation_chain: List[int] = []
    data_hash: str
    message_data: Sequence[MessageData]
    prompt_type: str
    prompt_category: str
    llm_model: LLModels
    usage: Optional[LLMUsage] = None
    call_chain_category: MessageCallChainCategory


class MessageThreadDTO(MessageThreadData):
    id: int
    created_at: datetime
    updated_at: datetime
