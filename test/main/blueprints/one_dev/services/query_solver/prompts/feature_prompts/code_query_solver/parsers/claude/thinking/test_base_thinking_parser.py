import pytest

from app.backend_common.services.llm.dataclasses.main import TextBlockDelta, TextBlockDeltaContent
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    ThinkingBlockDelta,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.claude.thinking.base_thinking_parser import (
    ThinkingParser,
)


@pytest.mark.asyncio
async def test_thinking_parser_basic_flow() -> None:
    parser = ThinkingParser()

    # First chunk should produce a start and a delta
    event1 = TextBlockDelta(content=TextBlockDeltaContent(text="Step 1 reasoning. "))
    results1 = await parser.parse_text_delta(event1)
    assert any(isinstance(r, ThinkingBlockStart) for r in results1)
    assert any(isinstance(r, ThinkingBlockDelta) for r in results1)

    # Next chunk should only produce a delta
    event2 = TextBlockDelta(content=TextBlockDeltaContent(text="Step 2 reasoning. "))
    results2 = await parser.parse_text_delta(event2)
    assert len(results2) == 1
    assert isinstance(results2[0], ThinkingBlockDelta)
    assert "Step 2" in results2[0].content.thinking_delta

    # Final flush should add a delta + end
    event3 = TextBlockDelta(content=TextBlockDeltaContent(text="Final thoughts."))
    results3 = await parser.parse_text_delta(event3, last_event=True)
    assert any(isinstance(r, ThinkingBlockDelta) for r in results3)
    assert any(isinstance(r, ThinkingBlockEnd) for r in results3)


@pytest.mark.asyncio
async def test_thinking_parser_empty_text() -> None:
    parser = ThinkingParser()

    # If content is empty, only start and end should appear
    event = TextBlockDelta(content=TextBlockDeltaContent(text=""))
    results = await parser.parse_text_delta(event, last_event=True)

    assert any(isinstance(r, ThinkingBlockStart) for r in results)
    assert not any(isinstance(r, ThinkingBlockDelta) for r in results)
    assert any(isinstance(r, ThinkingBlockEnd) for r in results)
