import pytest
from deputydev_core.llm_handler.dataclasses.main import TextBlockDelta, TextBlockDeltaContent

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    SummaryBlockDelta,
    SummaryBlockEnd,
    SummaryBlockStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.claude.summary.base_summary_parser import (
    SummaryParser,
)


@pytest.mark.asyncio
async def test_summary_parser_basic_flow() -> None:
    parser = SummaryParser()

    # First event should trigger SummaryBlockStart and SummaryBlockDelta
    event1 = TextBlockDelta(content=TextBlockDeltaContent(text="This is part 1. "))
    results1 = await parser.parse_text_delta(event1)
    assert any(isinstance(r, SummaryBlockStart) for r in results1)
    assert any(isinstance(r, SummaryBlockDelta) for r in results1)
    assert results1[1].content.summary_delta == "This is part 1. "

    # Another chunk (no new start, just delta)
    event2 = TextBlockDelta(content=TextBlockDeltaContent(text="And part 2."))
    results2 = await parser.parse_text_delta(event2)
    assert len(results2) == 1
    assert isinstance(results2[0], SummaryBlockDelta)
    assert "part 2" in results2[0].content.summary_delta

    # Final chunk with last_event=True should include SummaryBlockEnd
    event3 = TextBlockDelta(content=TextBlockDeltaContent(text=" Done."))
    results3 = await parser.parse_text_delta(event3, last_event=True)
    assert any(isinstance(r, SummaryBlockDelta) for r in results3)
    assert any(isinstance(r, SummaryBlockEnd) for r in results3)


@pytest.mark.asyncio
async def test_summary_parser_empty_text() -> None:
    parser = SummaryParser()

    # Send empty text (still should start block but no delta)
    event = TextBlockDelta(content=TextBlockDeltaContent(text=""))
    results = await parser.parse_text_delta(event, last_event=True)

    assert any(isinstance(r, SummaryBlockStart) for r in results)
    assert not any(isinstance(r, SummaryBlockDelta) for r in results)
    assert any(isinstance(r, SummaryBlockEnd) for r in results)
