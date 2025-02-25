from asyncio import Task
from enum import Enum
from typing import Annotated, Any, AsyncIterator, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    LLMUsage,
    ResponseData,
)


class LLMCallResponseTypes(Enum):
    NON_STREAMING = "NON_STREAMING"
    STREAMING = "STREAMING"


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
    content: Union[str, List[Dict[str, Any]]]


class ConversationTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class PromptCacheConfig(BaseModel):
    conversation: bool
    tools: bool
    system_message: bool


# ALL CONTENT BLOCK TYPES
class StreamingEventType(Enum):
    TEXT_BLOCK_START = "TEXT_START"
    TEXT_BLOCK_DELTA = "TEXT_DELTA"
    TEXT_BLOCK_END = "TEXT_BLOCK_END"
    TOOL_USE_REQUEST_START = "TOOL_USE_REQUEST_START"
    TOOL_USE_REQUEST_DELTA = "TOOL_USE_REQUEST_DELTA"
    TOOL_USE_REQUEST_END = "TOOL_USE_REQUEST_END"
    THINKING_BLOCK_START = "THINKING_BLOCK_START"
    THINKING_BLOCK_DELTA = "THINKING_BLOCK_DELTA"
    THINKING_BLOCK_END = "THINKING_BLOCK_END"
    CODE_BLOCK_START = "CODE_BLOCK_START"
    CODE_BLOCK_DELTA = "CODE_BLOCK_DELTA"
    CODE_BLOCK_END = "CODE_BLOCK_END"


# TOOL_USE_REQUEST BLOCK CONTENTS
class ToolUseRequestStartContent(BaseModel):
    tool_name: str
    tool_use_id: str


class ToolUseRequestDeltaContent(BaseModel):
    input_params_json_delta: str


# TEXT_BLOCK CONTENTS
class TextBlockDeltaContent(BaseModel):
    text: str


# STREAMING CONTENT BLOCKS

# TEXT BLOCKS
class TextBlockStart(BaseModel):
    type: Literal[StreamingEventType.TEXT_BLOCK_START] = StreamingEventType.TEXT_BLOCK_START


class TextBlockDelta(BaseModel):
    type: Literal[StreamingEventType.TEXT_BLOCK_DELTA] = StreamingEventType.TEXT_BLOCK_DELTA
    content: TextBlockDeltaContent


class TextBlockEnd(BaseModel):
    type: Literal[StreamingEventType.TEXT_BLOCK_END] = StreamingEventType.TEXT_BLOCK_END


# TOOL USE REQUEST BLOCKS
class ToolUseRequestStart(BaseModel):
    type: Literal[StreamingEventType.TOOL_USE_REQUEST_START] = StreamingEventType.TOOL_USE_REQUEST_START
    content: ToolUseRequestStartContent


class ToolUseRequestDelta(BaseModel):
    type: Literal[StreamingEventType.TOOL_USE_REQUEST_DELTA] = StreamingEventType.TOOL_USE_REQUEST_DELTA
    content: ToolUseRequestDeltaContent


class ToolUseRequestEnd(BaseModel):
    type: Literal[StreamingEventType.TOOL_USE_REQUEST_END] = StreamingEventType.TOOL_USE_REQUEST_END


TextBlockEvents = Annotated[Union[TextBlockStart, TextBlockDelta, TextBlockEnd], Field(discriminator="type")]
ToolUseRequestEvents = Annotated[
    Union[ToolUseRequestStart, ToolUseRequestDelta, ToolUseRequestEnd], Field(discriminator="type")
]


StreamingEvent = Annotated[
    Union[
        TextBlockEvents,
        ToolUseRequestEvents,
    ],
    Field(discriminator="type"),
]


class StreamingResponse(BaseModel):
    type: Literal[LLMCallResponseTypes.STREAMING]
    content: AsyncIterator[StreamingEvent]
    usage: Task[LLMUsage]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NonStreamingResponse(BaseModel):
    type: Literal[LLMCallResponseTypes.NON_STREAMING]
    content: List[ResponseData]
    usage: LLMUsage


UnparsedLLMCallResponse = Annotated[
    Union[StreamingResponse, NonStreamingResponse],
    Field(discriminator="type"),
]


class ParsedLLMCallResponseCommon(BaseModel):
    prompt_vars: Dict[str, Any]
    prompt_id: str
    model_used: LLModels


class StreamingParsedLLMCallResponse(ParsedLLMCallResponseCommon, StreamingResponse):
    parsed_content: AsyncIterator[Any]


class NonStreamingParsedLLMCallResponse(ParsedLLMCallResponseCommon, NonStreamingResponse):
    parsed_content: List[Any]


ParsedLLMCallResponse = Annotated[
    Union[
        StreamingParsedLLMCallResponse,
        NonStreamingParsedLLMCallResponse,
    ],
    Field(discriminator="type"),
]
