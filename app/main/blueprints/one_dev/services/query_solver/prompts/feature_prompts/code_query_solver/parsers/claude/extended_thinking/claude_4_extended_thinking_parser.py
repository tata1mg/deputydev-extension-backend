from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)
from deputydev_core.llm_handler.dataclasses.main import (
    ExtendedThinkingBlockDelta,
    ExtendedThinkingBlockEnd,
    ExtendedThinkingBlockStart,
)


class Claude4ExtendedThinkingParser:
    def parse(
        self, event: ExtendedThinkingBlockStart | ExtendedThinkingBlockDelta | ExtendedThinkingBlockEnd
    ) -> ThinkingBlockDelta | ThinkingBlockStart | ThinkingBlockEnd:
        if isinstance(event, ExtendedThinkingBlockStart):
            return ThinkingBlockStart()
        if isinstance(event, ExtendedThinkingBlockDelta):
            return ThinkingBlockDelta(content=ThinkingBlockDeltaContent(thinking_delta=event.content.thinking_delta))
        if isinstance(event, ExtendedThinkingBlockEnd):
            return ThinkingBlockEnd()
