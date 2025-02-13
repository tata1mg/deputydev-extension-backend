from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict

from app.common.constants.constants import LLModels


class LLMUsage(BaseModel):
    input: int
    output: int
    cache_read: Optional[int] = None
    cache_write: Optional[int] = None


class LLMMeta(BaseModel):
    llm_model: LLModels
    prompt_type: str
    token_usage: LLMUsage


class UserAndSystemMessages(BaseModel):
    user_message: str
    system_message: Optional[str] = None


class ConversationRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ConversationTurn(BaseModel):
    role: ConversationRole
    content: str


class ConversationTools(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class PromptCacheConfig(BaseModel):
    conversation: bool
    tools: bool
    system_message: bool


class StreamingContentBlockType(Enum):
    TEXT_DELTA = "TEXT_DELTA"
    TOOL_USE_REQUEST = "TOOL_USE_REQUEST"


class ToolUseRequest(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]


class StreamingContentBlock(BaseModel):
    type: StreamingContentBlockType
    content: Union[str, ToolUseRequest]


class StreamingResponse(BaseModel):
    content: AsyncIterator[StreamingContentBlock]
    usage: LLMUsage

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NonStreamingResponse(BaseModel):
    content: str
    tools: List[ToolUseRequest]
    usage: LLMUsage


class LLMCallResponse(BaseModel):
    raw_llm_response: Union[str, AsyncIterator[StreamingContentBlock]]
    parsed_llm_data: Optional[Dict[str, Any]]
    raw_prompt: str
    llm_meta: LLMMeta

    model_config = ConfigDict(arbitrary_types_allowed=True)
