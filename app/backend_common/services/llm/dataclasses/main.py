from asyncio import Task
from enum import Enum
from typing import (
    Annotated,
    Any,
    AsyncIterator,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ConfigDict, Field


class LLMCallResponseTypes(Enum):
    NON_STREAMING = "NON_STREAMING"
    STREAMING = "STREAMING"


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


class ConversationTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class PromptCacheConfig(BaseModel):
    conversation: bool
    tools: bool
    system_message: bool


class ContentBlockCategory(Enum):
    TEXT_BLOCK = "TEXT_BLOCK"
    TOOL_USE_REQUEST = "TOOL_USE_REQUEST"


# ALL CONTENT BLOCK TYPES
class StreamingContentBlockType(Enum):
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
    type: Literal[StreamingContentBlockType.TEXT_BLOCK_START]


class TextBlockDelta(BaseModel):
    type: Literal[StreamingContentBlockType.TEXT_BLOCK_DELTA]
    content: TextBlockDeltaContent


class TextBlockEnd(BaseModel):
    type: Literal[StreamingContentBlockType.TEXT_BLOCK_END]


# TOOL USE REQUEST BLOCKS
class ToolUseRequestStart(BaseModel):
    type: Literal[StreamingContentBlockType.TOOL_USE_REQUEST_START]
    content: ToolUseRequestStartContent


class ToolUseRequestDelta(BaseModel):
    type: Literal[StreamingContentBlockType.TOOL_USE_REQUEST_DELTA]
    content: ToolUseRequestDeltaContent


class ToolUseRequestEnd(BaseModel):
    type: Literal[StreamingContentBlockType.TOOL_USE_REQUEST_END]


StreamingContentBlock = Annotated[
    Union[
        TextBlockStart,
        TextBlockDelta,
        TextBlockEnd,
        ToolUseRequestStart,
        ToolUseRequestDelta,
        ToolUseRequestEnd,
    ],
    Field(discriminator="type"),
]


class StreamingResponse(BaseModel):
    type: Literal[LLMCallResponseTypes.STREAMING]
    content: AsyncIterator[StreamingContentBlock]
    usage: Task[LLMUsage]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NonStreamingTextBlockContent(BaseModel):
    text: str


class NonStreamingToolUseRequestContent(BaseModel):
    tool_input: Dict[str, Any]
    tool_name: str
    tool_use_id: str


class NonStreamingTextBlock(BaseModel):
    type: Literal[ContentBlockCategory.TEXT_BLOCK]
    content: NonStreamingTextBlockContent


class NonStreamingToolUseRequest(BaseModel):
    type: Literal[ContentBlockCategory.TOOL_USE_REQUEST]
    content: NonStreamingToolUseRequestContent


NonStreamingContentBlock = Annotated[
    Union[
        NonStreamingTextBlock,
        NonStreamingToolUseRequest,
    ],
    Field(discriminator="type"),
]


class NonStreamingResponse(BaseModel):
    type: Literal[LLMCallResponseTypes.NON_STREAMING]
    content: List[NonStreamingContentBlock]
    usage: LLMUsage


UnparsedLLMCallResponse = Annotated[
    Union[StreamingResponse, NonStreamingResponse],
    Field(discriminator="type"),
]


ParsedStreamingContentBlock = TypeVar("ParsedStreamingContentBlock")


class ParsedLLMCallResponseCommon(BaseModel):
    prompt_vars: Dict[str, Any]
    prompt_id: str
    model_used: LLModels


class StreamingParsedLLMCallResponse(
    ParsedLLMCallResponseCommon, StreamingResponse, Generic[ParsedStreamingContentBlock]
):
    parsed_content: AsyncIterator[ParsedStreamingContentBlock]


ParsedContentBlock = TypeVar("ParsedContentBlock")


class NonStreamingParsedLLMCallResponse(ParsedLLMCallResponseCommon, NonStreamingResponse, Generic[ParsedContentBlock]):
    parsed_content: List[ParsedContentBlock]


ParsedLLMCallResponse = Annotated[
    Union[
        StreamingParsedLLMCallResponse[ParsedStreamingContentBlock],
        NonStreamingParsedLLMCallResponse[ParsedContentBlock],
    ],
    Field(discriminator="type"),
]
