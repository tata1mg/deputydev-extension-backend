import re
from typing import Any, AsyncIterator, List, Optional

from app.backend_common.services.llm.dataclasses.main import (
    LLModels,
    StreamingEvent,
    TextBlockDelta,
    TextBlockDeltaContent,
    TextBlockEnd,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.providers.anthropic.prompts.parsers.event_based.text_block_xml_parser import (
    BaseAnthropicTextDeltaParser,
)


class BaseClaude3Point5SonnetPrompt(BasePrompt):
    model_name = LLModels.CLAUDE_3_POINT_5_SONNET

    @classmethod
    async def parse_streaming_events(
        cls, events: AsyncIterator[StreamingEvent], parsers: List[BaseAnthropicTextDeltaParser]
    ) -> AsyncIterator[Any]:
        xml_tags = {parser.xml_tag: parser for parser in parsers}

        text_buffer = ""
        tag_content_start_index: Optional[int] = None
        tag_content_end_index: Optional[int] = None

        current_ongoing_tag: Optional[str] = None  # this variable will store the current ongoing tag. Eg. some_tag

        # iterate over events and parse text blocks, if text block doesn't contain any xml tags, yield it, otherwise
        # keep accumulating text until we find full xml tag, then parse it and yield the result

        async for event in events:
            # start and end events are always yielded, because they don't contain any text
            if not isinstance(event, TextBlockDelta):
                yield event.model_dump(mode="json")
                continue

            text_buffer += event.content.text

            # if there is no ongoing tag, we try to find a new tag in the text, otherwise we keep yielding text
            # we use regex to find the tag, because partial tags are possible
            if current_ongoing_tag is None:
                # try to set current ongoing start tags
                for xml_tag, parser in xml_tags.items():
                    if parser.start_tag in text_buffer and (
                        tag_content_start_index is None or text_buffer.index(parser.start_tag) < tag_content_start_index
                    ):
                        current_ongoing_tag = xml_tag
                        tag_content_start_index = text_buffer.index(parser.start_tag)
                        continue

                    # match the partial start tag at the end of the text
                    ends_with_start_tag = re.search(parser.ends_with_start_tag_regex, text_buffer)
                    if bool(ends_with_start_tag):
                        tag_content_start_index = (
                            min(tag_content_start_index, text_buffer.index(ends_with_start_tag.group(0)))
                            if tag_content_start_index is not None
                            else text_buffer.index(ends_with_start_tag.group(0))
                        )
                        # breaking as we don't need to check for other tags, as even if the tag is some other tag, the partial value will be same
                        break

            else:
                # if a current ongoing tag is present, we try to end the tag
                ongoing_tag_parser = xml_tags[current_ongoing_tag]

                # check if the current ongoing tag ends in the text
                if ongoing_tag_parser.end_tag in text_buffer and (
                    tag_content_end_index is None
                    or text_buffer.index(ongoing_tag_parser.end_tag) + len(ongoing_tag_parser.end_tag)
                    > tag_content_end_index
                ):
                    tag_content_end_index = text_buffer.index(ongoing_tag_parser.end_tag) + len(
                        ongoing_tag_parser.end_tag
                    )
                    continue

                ends_with_end_tag = re.search(ongoing_tag_parser.ends_with_end_tag_regex, text_buffer)
                if bool(ends_with_end_tag):
                    tag_content_end_index = (
                        max(
                            tag_content_end_index,
                            text_buffer.index(ends_with_end_tag.group(0)) + len(ends_with_end_tag.group(0)),
                        )
                        if tag_content_end_index is not None
                        else text_buffer.index(ends_with_end_tag.group(0)) + len(ends_with_end_tag.group(0))
                    )

            ongoing_tag_parser = xml_tags[current_ongoing_tag] if current_ongoing_tag is not None else None
            # if there's a start index, we can yield the text before the start index
            if tag_content_start_index and tag_content_start_index > 0 and ongoing_tag_parser:
                yield TextBlockDelta(content=TextBlockDeltaContent(text=text_buffer[:tag_content_start_index])).model_dump(mode="json")
                yield TextBlockEnd().model_dump(mode="json")
                text_buffer = text_buffer[tag_content_start_index:]
                tag_content_start_index = 0
                tag_content_end_index = (
                    tag_content_end_index - tag_content_start_index if tag_content_end_index is not None else None
                )

            # if there's no start index and no ongoing tag, we yield the text and clear the buffer
            if tag_content_start_index is None and ongoing_tag_parser is None:
                yield TextBlockDelta(content=TextBlockDeltaContent(text=text_buffer)).model_dump(mode="json")
                text_buffer = ""

            # if there's no start index and a tag is ongoing, we yield the text after the end index
            if tag_content_start_index == 0 and tag_content_end_index is not None and ongoing_tag_parser is not None:
                tag_content = text_buffer[:tag_content_end_index]
                custom_event = await ongoing_tag_parser.parse_text_delta(
                    TextBlockDelta(content=TextBlockDeltaContent(text=tag_content))
                )
                if custom_event is not None:
                    yield custom_event
                text_buffer = text_buffer[tag_content_end_index:]
                tag_content_start_index = None
                tag_content_end_index = None
                current_ongoing_tag = None

            # if there's no start index and an ongoing tag, but no end index, we keep parsing using the parser and yielding the results
            if tag_content_start_index == 0 and tag_content_end_index is None and ongoing_tag_parser is not None:
                tag_content = text_buffer
                custom_event = await ongoing_tag_parser.parse_text_delta(
                    TextBlockDelta(content=TextBlockDeltaContent(text=tag_content))
                )
                if custom_event is not None:
                    yield custom_event
                text_buffer = ""
                tag_content_start_index = None
                tag_content_end_index = None
