# THINKING BLOCKS
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.backend_common.services.llm.dataclasses.main import (
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)


class StreamingContentBlockType(Enum):
    THINKING_BLOCK_START = "THINKING_BLOCK_START"
    THINKING_BLOCK_DELTA = "THINKING_BLOCK_DELTA"
    THINKING_BLOCK_END = "THINKING_BLOCK_END"
    CODE_BLOCK_START = "CODE_BLOCK_START"
    CODE_BLOCK_DELTA = "CODE_BLOCK_DELTA"
    CODE_BLOCK_END = "CODE_BLOCK_END"


# CODE_BLOCK CONTENTS
class CodeBlockStartContent(BaseModel):
    language: str
    filepath: str
    is_diff: bool


class CodeBlockDeltaContent(BaseModel):
    code_delta: str


# THINKING_BLOCK CONTENTS
class ThinkingBlockDeltaContent(BaseModel):
    thinking_delta: str


class ThinkingBlockStart(BaseModel):
    type: Literal[StreamingContentBlockType.THINKING_BLOCK_START] = StreamingContentBlockType.THINKING_BLOCK_START


class ThinkingBlockDelta(BaseModel):
    type: Literal[StreamingContentBlockType.THINKING_BLOCK_DELTA] = StreamingContentBlockType.THINKING_BLOCK_DELTA
    content: ThinkingBlockDeltaContent


class ThinkingBlockEnd(BaseModel):
    type: Literal[StreamingContentBlockType.THINKING_BLOCK_END] = StreamingContentBlockType.THINKING_BLOCK_END


# CODE BLOCKS
class CodeBlockStart(BaseModel):
    type: Literal[StreamingContentBlockType.CODE_BLOCK_START] = StreamingContentBlockType.CODE_BLOCK_START
    content: CodeBlockStartContent


class CodeBlockDelta(BaseModel):
    type: Literal[StreamingContentBlockType.CODE_BLOCK_DELTA] = StreamingContentBlockType.CODE_BLOCK_DELTA
    content: CodeBlockDeltaContent


class CodeBlockEnd(BaseModel):
    type: Literal[StreamingContentBlockType.CODE_BLOCK_END] = StreamingContentBlockType.CODE_BLOCK_END


StreamingContentBlock = Annotated[
    Union[
        TextBlockStart,
        TextBlockDelta,
        TextBlockEnd,
        ToolUseRequestStart,
        ToolUseRequestDelta,
        ToolUseRequestEnd,
        ThinkingBlockStart,
        ThinkingBlockDelta,
        ThinkingBlockEnd,
        CodeBlockStart,
        CodeBlockDelta,
        CodeBlockEnd,
    ],
    Field(discriminator="type"),
]
