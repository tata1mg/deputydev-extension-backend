import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel
from pydantic_core import from_json

from app.backend_common.services.llm.dataclasses.main import (
    StreamingEvent,
    StreamingEventType,
    TextBlockDelta,
    TextBlockDeltaContent,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockDeltaContent,
    CodeBlockEnd,
    CodeBlockEndContent,
    CodeBlockStart,
    CodeBlockStartContent,
    StreamingContentBlock,
    SummaryBlockDelta,
    SummaryBlockDeltaContent,
    SummaryBlockEnd,
    SummaryBlockStart,
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)


class ToolUseEventParser:
    def can_parse(self, event: StreamingEvent) -> bool:
        return isinstance(event, (ToolUseRequestStart, ToolUseRequestEnd, ToolUseRequestDelta))

    async def parse(self, event: StreamingEvent) -> AsyncIterator[Union[StreamingEvent, BaseModel]]:
        yield event


class TextBlockParser:
    def __init__(self) -> None:
        self.status = "NOT_STARTED"

    def parse(self, content: str, last_index: int) -> Tuple[List[StreamingContentBlock], int]:
        events: List[StreamingContentBlock] = []
        if self.status == "NOT_STARTED":
            events.append(TextBlockStart())
            self.status = "STARTED"
        if content[last_index:]:
            events.append(TextBlockDelta(content=TextBlockDeltaContent(text=content[last_index:])))
        return events, len(content)

    def end(self) -> List[StreamingContentBlock]:
        self.status = "NOT_STARTED"
        return [TextBlockEnd()]


class CodeBlockParser:
    def __init__(self) -> None:
        self.status = "NOT_STARTED"
        self.diff_buffer = ""
        self.diff_line_buffer = ""
        self.added_lines = 0
        self.removed_lines = 0
        self.is_diff = False
        self.udiff_line_start: Optional[str] = None
        self.text_buffer = ""

    def find_newline_instances(self, input_string: str) -> List[Tuple[int, int]]:
        # Regular expression to match either \n or \r\n
        pattern = r"\r?\n"

        # Find all matches
        matches = [(m.start(), m.end()) for m in re.finditer(pattern, input_string)]

        return matches

    def _get_udiff_line_start(self, line_data: str) -> Optional[str]:
        if line_data.startswith("@@"):
            return "@@"
        if line_data.startswith("---"):
            return "---"
        if line_data.startswith("+++"):
            return "+++"
        if line_data.startswith(" "):
            return " "
        if line_data.startswith("+"):
            return "+"
        if line_data.startswith("-"):
            return "-"
        return None

    def parse(self, part: Dict[str, Any], last_index: int) -> Tuple[List[StreamingContentBlock], int]:
        events: List[StreamingContentBlock] = []
        if self.status == "NOT_STARTED":
            events.append(
                CodeBlockStart(
                    content=CodeBlockStartContent(
                        language=part.get("language"), filepath=part.get("file_path"), is_diff=part.get("is_diff")
                    )
                )
            )
            self.status = "STARTED"
        delta = part["code"][last_index:]
        self.is_diff = part.get("is_diff")
        if not self.is_diff:
            if delta:
                events.append(CodeBlockDelta(content=CodeBlockDeltaContent(code_delta=delta)))
        else:
            self.diff_line_buffer += delta
            self.diff_buffer += delta
            if self.udiff_line_start:
                # end current udiff line if we have reached the end of the line
                # in case the line buffer contains a newline character
                newline_instances = self.find_newline_instances(self.diff_line_buffer)
                while newline_instances:
                    start, end = newline_instances.pop(0)
                    pre_line_part = self.diff_line_buffer[:start]
                    self.diff_line_buffer = self.diff_line_buffer[end:]
                    newline_instances = self.find_newline_instances(self.diff_line_buffer)
                    if self.udiff_line_start in [" ", "+"]:
                        self.text_buffer += (
                            pre_line_part.replace(f"{self.udiff_line_start}", "", 1) + "\n"
                        )  # replace only the first instance of the udiff line start
                        if self.udiff_line_start == "+":
                            self.added_lines += 1
                    if self.udiff_line_start == "-":
                        self.removed_lines += 1
                    self.udiff_line_start = self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
            self.udiff_line_start = self._get_udiff_line_start(self.diff_line_buffer.lstrip("\n\r"))
            if self.text_buffer:
                events.append(CodeBlockDelta(content=CodeBlockDeltaContent(code_delta=self.text_buffer)))
            self.text_buffer = ""
        return events, len(part["code"])

    def end(self) -> List[StreamingContentBlock]:
        end_content = CodeBlockEndContent()
        if self.is_diff:
            end_content.diff = self.diff_buffer
            end_content.added_lines = self.added_lines
            end_content.removed_lines = self.removed_lines

        # reset parser
        self.status = "NOT_STARTED"
        self.complete_code_block = ""
        self.diff_buffer = ""
        self.added_lines = 0
        self.removed_lines = 0
        self.is_diff = False

        return [CodeBlockEnd(content=end_content)]


class ResponsePartParser:
    def __init__(self) -> None:
        self.text_parser = TextBlockParser()
        self.code_parser = CodeBlockParser()
        self.current_type = None

    def parse_helper(self, part: Dict[str, Any], last_index: int = 0) -> Tuple[List[StreamingContentBlock], int]:
        if part.get("type") == "text" and part.get("content"):
            self.current_type = "text"
            return self.text_parser.parse(part["content"], last_index)
        elif part.get("type") == "code_block" and part.get("code"):
            self.current_type = "code_block"
            return self.code_parser.parse(part, last_index)
        return [], last_index

    def end_current_block(self) -> List[StreamingContentBlock]:
        if self.current_type == "text":
            return self.text_parser.end()
        elif self.current_type == "code_block":
            return self.code_parser.end()
        return []

    def parse(
        self, response_parts: List[Dict[str, Any]], last_index: int = 0, last_processed: int = 0
    ) -> Tuple[List[StreamingEvent], int, int]:
        old_events, new_events = [], []

        if last_processed < len(response_parts) - 1:
            old_events, last_index = self.parse_helper(response_parts[-2], last_index)
            old_events += self.end_current_block()
            last_index = 0
            self.current_type = None

        if response_parts:
            new_events, last_index = self.parse_helper(response_parts[-1], last_index)

        last_processed = max(0, len(response_parts) - 1)
        return old_events + new_events, last_index, last_processed


class TextBlockEventParser:
    def __init__(self) -> None:
        self.buffer = ""
        self.prev_block = ""
        self.current_block = ""
        self.parsed_index = 0
        self.last_processed_response_block = 0
        self.response_parser = ResponsePartParser()
        self.thinking_parser = ThinkingBlockParser()
        self.summary_parser = SummaryBlockParser()

    def can_parse(self, event: StreamingEvent) -> bool:
        return isinstance(event, (TextBlockStart, TextBlockDelta, TextBlockEnd))

    async def parse(self, event: StreamingEvent) -> AsyncIterator[Union[StreamingEvent, BaseModel]]:  # noqa: C901
        if event.type == StreamingEventType.TEXT_BLOCK_START:
            return

        if event.type == StreamingEventType.TEXT_BLOCK_END:
            if self.current_block == "response_parts":
                for e in self.response_parser.end_current_block():
                    yield e
            elif self.current_block == "thinking":
                for e in self.thinking_parser.close():
                    yield e
            elif self.current_block == "summary":
                for e in self.summary_parser.close():
                    yield e
            return

        self.buffer += event.content.text
        parsed_response = from_json(self.buffer, allow_partial=True)
        keys = list(parsed_response.keys())
        if keys:
            self.current_block = keys[-1]
            if not self.prev_block:
                self.prev_block = self.current_block

        if self.current_block != self.prev_block:
            async for event in self._handle_previous_block(parsed_response):
                yield event
            self.prev_block = self.current_block
            self.parsed_index = 0

        block_data = parsed_response.get(self.current_block, "")

        if self.current_block == "thinking":
            delta = block_data[self.parsed_index :]
            parsed_events = list(self.thinking_parser.parse(delta))
            for e in parsed_events:
                yield e
            self.parsed_index = len(block_data)

        elif self.current_block == "summary":
            delta = block_data[self.parsed_index :]
            for e in self.summary_parser.parse(delta):
                yield e
            self.parsed_index = len(block_data)

        elif self.current_block == "response_parts":
            events, self.parsed_index, self.last_processed_response_block = self.response_parser.parse(
                parsed_response[self.current_block], self.parsed_index, self.last_processed_response_block
            )
            for e in events:
                yield e

    async def _handle_previous_block(self, parsed_response: Dict[str, Any]) -> AsyncIterator[StreamingContentBlock]:
        block_data = parsed_response.get(self.prev_block, "")
        if self.prev_block == "thinking":
            delta = block_data[self.parsed_index :]
            for e in self.thinking_parser.parse(delta):
                yield e
            for e in self.thinking_parser.close():
                yield e

        elif self.prev_block == "summary":
            delta = block_data[self.parsed_index :]
            for e in self.summary_parser.parse(delta):
                yield e
            for e in self.summary_parser.close():
                yield e

        elif self.prev_block == "response_parts":
            events, _, _ = self.response_parser.parse(
                parsed_response[self.prev_block], self.parsed_index, self.last_processed_response_block
            )
            events += self.response_parser.end_current_block()
            for e in events:
                yield e


class BaseBlockParser:
    def __init__(self) -> None:
        self.status = "NOT_STARTED"

    def start(self) -> bool:
        if self.status == "NOT_STARTED":
            self.status = "STARTED"
            return True
        return False

    def end(self) -> None:
        self.status = "NOT_STARTED"


class ThinkingBlockParser(BaseBlockParser):
    def parse(self, delta: str) -> List[StreamingEvent]:
        events = []
        if delta:
            if self.start():
                events.append(ThinkingBlockStart())
            events.append(ThinkingBlockDelta(content=ThinkingBlockDeltaContent(thinking_delta=delta)))
        return events

    def close(self) -> List[StreamingEvent]:
        if self.status == "STARTED":
            self.end()
            return [ThinkingBlockEnd()]
        return []


class SummaryBlockParser(BaseBlockParser):
    def parse(self, delta: str) -> List[StreamingEvent]:
        events = []
        if delta:
            if self.start():
                events.append(SummaryBlockStart())
            events.append(SummaryBlockDelta(content=SummaryBlockDeltaContent(summary_delta=delta)))
        return events

    def close(self) -> List[StreamingEvent]:
        if self.status == "STARTED":
            self.end()
            return [SummaryBlockEnd()]
        return []


class StreamingTextEventProcessor:
    def __init__(self, parsers: List[Union[TextBlockEventParser, ToolUseEventParser]]) -> None:
        self.parsers = parsers

    async def parse(self, events: AsyncIterator[StreamingEvent]) -> AsyncIterator[Union[StreamingEvent, BaseModel]]:
        async for event in events:
            for parser in self.parsers:
                if parser.can_parse(event):
                    async for parsed_event in parser.parse(event):
                        yield parsed_event
                    break
