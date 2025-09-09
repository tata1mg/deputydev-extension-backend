# THINKING BLOCKS
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from deputydev_core.llm_handler.dataclasses.main import (
    MalformedToolUseRequest,
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
    SUMMARY_BLOCK_START = "SUMMARY_BLOCK_START"
    SUMMARY_BLOCK_DELTA = "SUMMARY_BLOCK_DELTA"
    SUMMARY_BLOCK_END = "SUMMARY_BLOCK_END"
    MALFORMED_TOOL_USE_REQUEST = "MALFORMED_TOOL_USE_REQUEST"


# CODE_BLOCK CONTENTS
class CodeBlockStartContent(BaseModel):
    language: str
    filepath: str
    is_diff: bool


class CodeBlockDeltaContent(BaseModel):
    code_delta: str


class CodeBlockEndContent(BaseModel):
    diff: Optional[str] = None
    added_lines: Optional[int] = None
    removed_lines: Optional[int] = None


# THINKING_BLOCK CONTENTS
class ThinkingBlockDeltaContent(BaseModel):
    thinking_delta: str


class ThinkingBlockStart(BaseModel):
    type: Literal[StreamingContentBlockType.THINKING_BLOCK_START] = StreamingContentBlockType.THINKING_BLOCK_START
    ignore_in_chat: Optional[bool] = False


class ThinkingBlockDelta(BaseModel):
    type: Literal[StreamingContentBlockType.THINKING_BLOCK_DELTA] = StreamingContentBlockType.THINKING_BLOCK_DELTA
    content: ThinkingBlockDeltaContent
    ignore_in_chat: Optional[bool] = False

    def __add__(self, other: "ThinkingBlockDelta") -> "ThinkingBlockDelta":
        return ThinkingBlockDelta(
            content=ThinkingBlockDeltaContent(thinking_delta=self.content.thinking_delta + other.content.thinking_delta)
        )


class ThinkingBlockEnd(BaseModel):
    type: Literal[StreamingContentBlockType.THINKING_BLOCK_END] = StreamingContentBlockType.THINKING_BLOCK_END
    ignore_in_chat: Optional[bool] = False


# CODE BLOCKS
class CodeBlockStart(BaseModel):
    type: Literal[StreamingContentBlockType.CODE_BLOCK_START] = StreamingContentBlockType.CODE_BLOCK_START
    content: CodeBlockStartContent


class CodeBlockDelta(BaseModel):
    type: Literal[StreamingContentBlockType.CODE_BLOCK_DELTA] = StreamingContentBlockType.CODE_BLOCK_DELTA
    content: CodeBlockDeltaContent

    def __add__(self, other: "CodeBlockDelta") -> "CodeBlockDelta":
        return CodeBlockDelta(
            content=CodeBlockDeltaContent(code_delta=self.content.code_delta + other.content.code_delta)
        )


class CodeBlockEnd(BaseModel):
    type: Literal[StreamingContentBlockType.CODE_BLOCK_END] = StreamingContentBlockType.CODE_BLOCK_END
    content: CodeBlockEndContent


# SUMMARY BLOCKS


class SummaryBlockDeltaContent(BaseModel):
    summary_delta: str


class SummaryBlockStart(BaseModel):
    type: Literal[StreamingContentBlockType.SUMMARY_BLOCK_START] = StreamingContentBlockType.SUMMARY_BLOCK_START


class SummaryBlockDelta(BaseModel):
    type: Literal[StreamingContentBlockType.SUMMARY_BLOCK_DELTA] = StreamingContentBlockType.SUMMARY_BLOCK_DELTA
    content: SummaryBlockDeltaContent

    def __add__(self, other: "SummaryBlockDelta") -> "SummaryBlockDelta":
        return SummaryBlockDelta(
            content=SummaryBlockDeltaContent(summary_delta=self.content.summary_delta + other.content.summary_delta)
        )


class SummaryBlockEnd(BaseModel):
    type: Literal[StreamingContentBlockType.SUMMARY_BLOCK_END] = StreamingContentBlockType.SUMMARY_BLOCK_END


StreamingContentBlock = Annotated[
    Union[
        TextBlockStart,
        TextBlockDelta,
        TextBlockEnd,
        ToolUseRequestStart,
        ToolUseRequestDelta,
        ToolUseRequestEnd,
        MalformedToolUseRequest,
        ThinkingBlockStart,
        ThinkingBlockDelta,
        ThinkingBlockEnd,
        CodeBlockStart,
        CodeBlockDelta,
        CodeBlockEnd,
        SummaryBlockStart,
        SummaryBlockDelta,
        SummaryBlockEnd,
    ],
    Field(discriminator="type"),
]
