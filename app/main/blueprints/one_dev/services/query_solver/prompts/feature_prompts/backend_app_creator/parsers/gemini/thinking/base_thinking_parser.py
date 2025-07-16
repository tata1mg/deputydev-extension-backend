from typing import List

from pydantic import BaseModel

from app.backend_common.services.llm.dataclasses.main import TextBlockDelta
from app.backend_common.services.llm.providers.google.prompts.parsers.event_based.text_block_xml_parser import (
    BaseGoogleTextDeltaParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.dataclasses.main import (
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)


class ThinkingParser(BaseGoogleTextDeltaParser):
    def __init__(self) -> None:
        super().__init__(xml_tag="thinking")

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:
        if not self.start_event_completed:
            self.event_buffer.append(ThinkingBlockStart())
            self.start_event_completed = True

        if event.content.text:
            self.event_buffer.append(
                ThinkingBlockDelta(content=ThinkingBlockDeltaContent(thinking_delta=event.content.text))
            )

        if last_event:
            self.event_buffer.append(ThinkingBlockEnd())

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return
