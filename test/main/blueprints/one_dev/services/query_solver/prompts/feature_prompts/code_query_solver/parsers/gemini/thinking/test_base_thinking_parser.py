import pytest
from typing import List
from unittest.mock import Mock

from pydantic import BaseModel

from app.backend_common.services.llm.dataclasses.main import TextBlockDelta, TextBlockDeltaContent
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.thinking.base_thinking_parser import (
    ThinkingParser,
)
from test.fixtures.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.thinking.base_thinking_parser_fixtures import (
    BaseThinkingParserFixtures,
)


class TestBaseThinkingParser:
    """Test suite for Gemini base ThinkingParser functionality."""

    @pytest.fixture
    def parser(self) -> ThinkingParser:
        """Create a fresh parser instance for each test."""
        return ThinkingParser()

    def create_text_delta(self, text: str) -> TextBlockDelta:
        """Helper method to create TextBlockDelta objects."""
        return TextBlockDelta(content=TextBlockDeltaContent(text=text))

    # =================================
    # BASIC FUNCTIONALITY TESTS
    # =================================

    @pytest.mark.asyncio
    async def test_parser_initialization(self, parser: ThinkingParser) -> None:
        """Test proper parser initialization."""
        assert parser.xml_tag == "thinking"
        assert parser.start_event_completed is False
        assert parser.event_buffer == []

    @pytest.mark.asyncio
    async def test_simple_thinking_block_parsing(self, parser: ThinkingParser) -> None:
        """Test parsing a simple thinking block."""
        thinking_text = "This is a simple thinking process."
        
        event = self.create_text_delta(thinking_text)
        results = await parser.parse_text_delta(event, last_event=True)
        
        # Should have start, delta, and end events
        assert len(results) == 3
        
        # Check ThinkingBlockStart
        assert isinstance(results[0], ThinkingBlockStart)
        
        # Check ThinkingBlockDelta
        assert isinstance(results[1], ThinkingBlockDelta)
        assert results[1].content.thinking_delta == thinking_text
        
        # Check ThinkingBlockEnd
        assert isinstance(results[2], ThinkingBlockEnd)

    @pytest.mark.asyncio
    async def test_multi_part_thinking_block(self, parser: ThinkingParser) -> None:
        """Test parsing thinking block across multiple events."""
        thinking_parts = [
            "First part of thinking: ",
            "I need to analyze the problem carefully. ",
            "Let me break this down into smaller steps.",
        ]
        
        all_deltas = []
        
        # Process all but the last part
        for part in thinking_parts[:-1]:
            event = self.create_text_delta(part)
            results = await parser.parse_text_delta(event)
            
            # First event should include start
            if not all_deltas:
                assert len(results) >= 1
                assert isinstance(results[0], ThinkingBlockStart)
                deltas = [r for r in results if isinstance(r, ThinkingBlockDelta)]
                all_deltas.extend(deltas)
            else:
                deltas = [r for r in results if isinstance(r, ThinkingBlockDelta)]
                all_deltas.extend(deltas)
        
        # Process final part with last_event=True
        final_event = self.create_text_delta(thinking_parts[-1])
        results = await parser.parse_text_delta(final_event, last_event=True)
        
        # Should include final delta and end
        final_deltas = [r for r in results if isinstance(r, ThinkingBlockDelta)]
        end_events = [r for r in results if isinstance(r, ThinkingBlockEnd)]
        
        all_deltas.extend(final_deltas)
        
        assert len(end_events) == 1
        assert len(all_deltas) >= 1
        
        # Verify content is preserved
        combined_thinking = "".join([delta.content.thinking_delta for delta in all_deltas])
        expected_thinking = "".join(thinking_parts)
        assert combined_thinking == expected_thinking

    @pytest.mark.asyncio
    async def test_empty_thinking_block(self, parser: ThinkingParser) -> None:
        """Test parsing an empty thinking block."""
        event = self.create_text_delta("")
        results = await parser.parse_text_delta(event, last_event=True)
        
        # Should still have start and end, but no delta
        start_events = [r for r in results if isinstance(r, ThinkingBlockStart)]
        delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
        end_events = [r for r in results if isinstance(r, ThinkingBlockEnd)]
        
        assert len(start_events) == 1
        assert len(delta_events) == 0  # No delta for empty text
        assert len(end_events) == 1

    @pytest.mark.asyncio
    async def test_whitespace_only_thinking(self, parser: ThinkingParser) -> None:
        """Test parsing thinking block with only whitespace."""
        whitespace_text = "   \n\t  \n  "
        
        event = self.create_text_delta(whitespace_text)
        results = await parser.parse_text_delta(event, last_event=True)
        
        # Should preserve whitespace in delta
        delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
        assert len(delta_events) == 1
        assert delta_events[0].content.thinking_delta == whitespace_text

    # =================================
    # EDGE CASES AND ERROR HANDLING
    # =================================

    @pytest.mark.asyncio
    async def test_large_thinking_content(self, parser: ThinkingParser) -> None:
        """Test parsing large thinking content."""
        large_content = BaseThinkingParserFixtures.get_large_thinking_content()
        
        event = self.create_text_delta(large_content)
        results = await parser.parse_text_delta(event, last_event=True)
        
        # Should handle large content properly
        delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
        assert len(delta_events) == 1
        assert delta_events[0].content.thinking_delta == large_content

    @pytest.mark.asyncio
    async def test_thinking_with_special_characters(self, parser: ThinkingParser) -> None:
        """Test parsing thinking with special characters."""
        special_chars_examples = BaseThinkingParserFixtures.get_special_characters_examples()
        
        for special_text in special_chars_examples:
            # Reset parser for each test
            parser.start_event_completed = False
            parser.event_buffer = []
            
            event = self.create_text_delta(special_text)
            results = await parser.parse_text_delta(event, last_event=True)
            
            # Should preserve special characters
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            if special_text:  # Only check if text is not empty
                assert len(delta_events) == 1
                assert delta_events[0].content.thinking_delta == special_text

    @pytest.mark.asyncio
    async def test_incremental_thinking_parsing(self, parser: ThinkingParser) -> None:
        """Test incremental parsing with character-by-character input."""
        thinking_text = "Gradual thinking process"
        
        all_deltas = []
        start_found = False
        
        # Process character by character
        for i, char in enumerate(thinking_text):
            is_last = (i == len(thinking_text) - 1)
            event = self.create_text_delta(char)
            results = await parser.parse_text_delta(event, last_event=is_last)
            
            # Check for start event in first iteration
            if not start_found:
                start_events = [r for r in results if isinstance(r, ThinkingBlockStart)]
                if start_events:
                    start_found = True
            
            # Collect delta events
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            all_deltas.extend(delta_events)
            
            # Check for end event in last iteration
            if is_last:
                end_events = [r for r in results if isinstance(r, ThinkingBlockEnd)]
                assert len(end_events) == 1
        
        # Verify all characters are captured
        combined_text = "".join([delta.content.thinking_delta for delta in all_deltas])
        assert combined_text == thinking_text
        assert start_found

    # =================================
    # STATE MANAGEMENT TESTS
    # =================================

    @pytest.mark.asyncio
    async def test_parser_state_after_completion(self, parser: ThinkingParser) -> None:
        """Test parser state after completing a thinking block."""
        event = self.create_text_delta("Test thinking")
        results = await parser.parse_text_delta(event, last_event=True)
        
        # After parsing, event buffer should be cleared
        assert parser.event_buffer == []
        # But start_event_completed should remain True until cleanup
        assert parser.start_event_completed is True

    @pytest.mark.asyncio
    async def test_cleanup_resets_state(self, parser: ThinkingParser) -> None:
        """Test that cleanup properly resets parser state."""
        # Process some content first
        event = self.create_text_delta("Some thinking")
        await parser.parse_text_delta(event, last_event=True)
        
        # Verify state is set
        assert parser.start_event_completed is True
        
        # Cleanup
        await parser.cleanup()
        
        # Verify state is reset
        assert parser.start_event_completed is False
        assert parser.event_buffer == []

    @pytest.mark.asyncio
    async def test_multiple_thinking_blocks_with_cleanup(self, parser: ThinkingParser) -> None:
        """Test parsing multiple thinking blocks with cleanup between them."""
        thinking_blocks = [
            "First thinking block content",
            "Second thinking block with different content",
            "Third block with more complex reasoning"
        ]
        
        for thinking_content in thinking_blocks:
            # Process thinking block
            event = self.create_text_delta(thinking_content)
            results = await parser.parse_text_delta(event, last_event=True)
            
            # Verify proper structure
            start_events = [r for r in results if isinstance(r, ThinkingBlockStart)]
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            end_events = [r for r in results if isinstance(r, ThinkingBlockEnd)]
            
            assert len(start_events) == 1
            assert len(delta_events) == 1
            assert len(end_events) == 1
            assert delta_events[0].content.thinking_delta == thinking_content
            
            # Cleanup for next iteration
            await parser.cleanup()

    # =================================
    # COMPLEX THINKING SCENARIOS
    # =================================

    @pytest.mark.asyncio
    async def test_structured_thinking_content(self, parser: ThinkingParser) -> None:
        """Test parsing structured thinking with bullets, numbers, etc."""
        structured_examples = BaseThinkingParserFixtures.get_structured_thinking_examples()
        
        for structured_content in structured_examples:
            # Reset parser
            await parser.cleanup()
            
            event = self.create_text_delta(structured_content)
            results = await parser.parse_text_delta(event, last_event=True)
            
            # Should preserve structure
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            assert len(delta_events) == 1
            assert delta_events[0].content.thinking_delta == structured_content

    @pytest.mark.asyncio
    async def test_thinking_with_code_snippets(self, parser: ThinkingParser) -> None:
        """Test thinking blocks that contain code snippets."""
        code_examples = BaseThinkingParserFixtures.get_thinking_with_code_examples()
        
        for code_thinking in code_examples:
            # Reset parser
            await parser.cleanup()
            
            event = self.create_text_delta(code_thinking)
            results = await parser.parse_text_delta(event, last_event=True)
            
            # Should preserve code snippets exactly
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            assert len(delta_events) == 1
            assert delta_events[0].content.thinking_delta == code_thinking

    @pytest.mark.asyncio
    async def test_multilingual_thinking(self, parser: ThinkingParser) -> None:
        """Test thinking blocks with non-English content."""
        multilingual_examples = BaseThinkingParserFixtures.get_multilingual_examples()
        
        for multilingual_content in multilingual_examples:
            # Reset parser
            await parser.cleanup()
            
            event = self.create_text_delta(multilingual_content)
            results = await parser.parse_text_delta(event, last_event=True)
            
            # Should preserve non-English characters
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            assert len(delta_events) == 1
            assert delta_events[0].content.thinking_delta == multilingual_content

    # =================================
    # PERFORMANCE AND RELIABILITY TESTS
    # =================================

    @pytest.mark.asyncio
    async def test_concurrent_parsing_simulation(self, parser: ThinkingParser) -> None:
        """Test parser behavior under rapid sequential events."""
        rapid_events = ["Fast ", "sequential ", "thinking ", "events ", "for ", "testing"]
        
        all_deltas = []
        
        for i, text in enumerate(rapid_events):
            is_last = (i == len(rapid_events) - 1)
            event = self.create_text_delta(text)
            results = await parser.parse_text_delta(event, last_event=is_last)
            
            delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
            all_deltas.extend(delta_events)
        
        # Verify all content is captured
        combined_text = "".join([delta.content.thinking_delta for delta in all_deltas])
        expected_text = "".join(rapid_events)
        assert combined_text == expected_text

    @pytest.mark.asyncio
    async def test_parser_memory_efficiency(self, parser: ThinkingParser) -> None:
        """Test that parser doesn't accumulate excessive state."""
        # Process several thinking blocks
        for i in range(10):
            event = self.create_text_delta(f"Thinking block {i}")
            results = await parser.parse_text_delta(event, last_event=True)
            
            # Event buffer should be cleared after each complete parsing
            assert parser.event_buffer == []
        
        # Final cleanup
        await parser.cleanup()
        assert parser.start_event_completed is False

    @pytest.mark.asyncio
    async def test_error_recovery(self, parser: ThinkingParser) -> None:
        """Test parser recovery from potential error states."""
        # Simulate some processing
        event1 = self.create_text_delta("First part")
        await parser.parse_text_delta(event1)
        
        # Force cleanup (simulate error recovery)
        await parser.cleanup()
        
        # Should be able to process new content
        event2 = self.create_text_delta("New thinking after cleanup")
        results = await parser.parse_text_delta(event2, last_event=True)
        
        # Should work normally
        start_events = [r for r in results if isinstance(r, ThinkingBlockStart)]
        delta_events = [r for r in results if isinstance(r, ThinkingBlockDelta)]
        end_events = [r for r in results if isinstance(r, ThinkingBlockEnd)]
        
        assert len(start_events) == 1
        assert len(delta_events) == 1
        assert len(end_events) == 1