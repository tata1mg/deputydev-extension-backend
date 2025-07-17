from typing import List

from pydantic import BaseModel

from app.backend_common.services.llm.dataclasses.main import (
    TextBlockDelta,
)
from app.backend_common.services.llm.providers.anthropic.prompts.parsers.event_based.text_block_xml_parser import (
    BaseAnthropicTextDeltaParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    SummaryBlockDelta,
    SummaryBlockDeltaContent,
    SummaryBlockEnd,
    SummaryBlockStart,
)


class SummaryParser(BaseAnthropicTextDeltaParser):
    def __init__(self) -> None:
        super().__init__(xml_tag="summary")

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:
        if not self.start_event_completed:
            self.event_buffer.append(SummaryBlockStart())
            self.start_event_completed = True

        if event.content.text:
            self.event_buffer.append(
                SummaryBlockDelta(content=SummaryBlockDeltaContent(summary_delta=event.content.text))
            )

        if last_event:
            self.event_buffer.append(SummaryBlockEnd())

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return
