from deputydev_core.llm_handler.dataclasses.main import (
    ExtendedThinkingBlockDelta,
    ExtendedThinkingBlockStart,
    ExtendedThinkingEvents,
)

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)


class GrokCodeFast1ReasoningThinkingParser:
    def parse(self, event: ExtendedThinkingEvents) -> ThinkingBlockStart | ThinkingBlockDelta | ThinkingBlockEnd:
        if isinstance(event, ExtendedThinkingBlockStart):
            return ThinkingBlockStart(ignore_in_chat=True)
        if isinstance(event, ExtendedThinkingBlockDelta):
            return ThinkingBlockDelta(
                content=ThinkingBlockDeltaContent(thinking_delta=event.content.thinking_delta), ignore_in_chat=True
            )
        else:  # ExtendedThinkingBlockEnd
            return ThinkingBlockEnd(ignore_in_chat=True)
