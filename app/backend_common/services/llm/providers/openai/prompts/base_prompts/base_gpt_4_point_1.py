import re
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import LLModels, MessageData
from app.backend_common.services.llm.dataclasses.main import (
    StreamingEvent,
    StreamingEventType,
    TextBlockDelta,
    TextBlockDeltaContent,
    TextBlockEnd,
    TextBlockEvents,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.providers.google.prompts.base_prompts.dataclasses.main import (
    XMLWrappedContentPosition,
    XMLWrappedContentTagPosition,
)
from app.backend_common.services.llm.providers.google.prompts.parsers.event_based.text_block_xml_parser import (
    BaseGoogleTextDeltaParser,
)


class BaseGpt4Point1Prompt(BasePrompt):
    model_name = LLModels.GPT_4_POINT_1

    @classmethod
    def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    async def parse_streaming_text_block_events(
        cls, events: AsyncIterator[StreamingEvent]
    ) -> AsyncIterator[Union[StreamingEvent, BaseModel]]:
        async for event in events:
            ################################################################################################################
            # Handling non TextBlockDelta events
            ################################################################################################################
            # if event is not text block, yield it
            if (
                isinstance(event, ToolUseRequestStart)
                or isinstance(event, ToolUseRequestEnd)
                or isinstance(event, ToolUseRequestDelta)
            ):
                yield event
                continue
