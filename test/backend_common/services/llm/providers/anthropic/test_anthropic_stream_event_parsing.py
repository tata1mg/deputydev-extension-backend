"""
Tests for Anthropic LLM Provider Stream Event Parsing.

This module comprehensively tests the Anthropic._get_parsed_stream_event method,
which is responsible for parsing various types of Anthropic stream events into
our internal streaming event format.

Test Categories:
- Message completion events (with/without usage)
- Tool use events (start, delta, end)
- Text block events (start, delta, end)
- Extended thinking events (start, delta, end)
- Edge cases and error handling
- Parametrized tests for various input combinations
- Sequence testing for complete event flows
- Type safety validation
"""

from typing import List, Optional, Tuple

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    ExtendedThinkingBlockDelta,
    ExtendedThinkingBlockEnd,
    ExtendedThinkingBlockStart,
    RedactedThinking,
    StreamingEvent,
    StreamingEventType,
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)

# Import required classes from message thread DTO and streaming dataclasses
from app.backend_common.models.dto.message_thread_dto import ContentBlockCategory, LLMUsage
from deputydev_core.llm_handler.providers.anthropic.llm_provider import Anthropic

# Import fixtures from organized fixture modules
from test.fixtures.anthropic import (
    create_input_json_delta_event,
    create_message_stop_event,
    create_text_delta_event,
    create_thinking_delta_event,
    create_tool_use_start_event,
)

# Use provider fixture that handles import properly


class TestAnthropicStreamEventParsing:
    """Test suite for Anthropic stream event parsing functionality."""

    # ===============================
    # MESSAGE COMPLETION TESTS
    # ===============================

    def test_message_stop_with_usage(self, anthropic_provider: Anthropic, mock_message_stop_event: dict) -> None:
        """Test parsing message_stop event with usage information."""
        result: Tuple[List[StreamingEvent], Optional[ContentBlockCategory], Optional[str], Optional[LLMUsage]] = (
            anthropic_provider._get_parsed_stream_event(
                mock_message_stop_event, current_content_block_delta="", current_running_block_type=None
            )
        )

        streaming_events, content_category, delta, usage = result

        # Should return empty list for streaming events and None for content category
        assert streaming_events == []
        assert content_category is None
        assert delta is None

        # Should return usage information
        assert usage is not None
        assert isinstance(usage, LLMUsage)
        assert usage.input == 100
        assert usage.output == 50
        assert usage.cache_read == 20
        assert usage.cache_write == 10

    def test_message_stop_without_usage(
        self, anthropic_provider: Anthropic, mock_message_stop_without_usage: dict
    ) -> None:
        """Test parsing message_stop event without usage information."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_message_stop_without_usage, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return empty lists/None when no usage data
        assert streaming_events == []
        assert content_category is None
        assert delta is None
        assert usage is not None  # Usage object is still created but with default values
        assert usage.input == 0
        assert usage.output == 0
        assert usage.cache_read == 0
        assert usage.cache_write == 0

    def test_message_stop_with_incomplete_usage(
        self, anthropic_provider: Anthropic, mock_message_stop_incomplete_usage: dict
    ) -> None:
        """Test parsing message_stop with incomplete usage data."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_message_stop_incomplete_usage, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should handle incomplete usage gracefully
        assert streaming_events == []
        assert content_category is None
        assert delta is None
        assert usage is not None
        assert usage.input == 50  # Available field
        assert usage.output == 0  # Missing field defaults to 0
        assert usage.cache_read == 0  # Missing field defaults to 0
        assert usage.cache_write == 0  # Missing field defaults to 0

    # ===============================
    # EXTENDED THINKING TESTS
    # ===============================

    def test_thinking_block_start_event(
        self, anthropic_provider: Anthropic, mock_thinking_block_start_event: dict
    ) -> None:
        """Test parsing content_block_start event for thinking blocks."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_thinking_block_start_event, current_content_block_delta="", current_running_block_type=None
        )
        # Note: thinking block start returns a 3-tuple instead of 4-tuple
        streaming_event, content_category, delta = result

        # Should return ExtendedThinkingBlockStart event as single object
        assert isinstance(streaming_event, ExtendedThinkingBlockStart)
        assert content_category == ContentBlockCategory.EXTENDED_THINKING
        assert delta is None

    def test_redacted_thinking_block_start_event(
        self, anthropic_provider: Anthropic, mock_redacted_thinking_block_start_event: dict
    ) -> None:
        """Test parsing content_block_start event for redacted thinking blocks."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_redacted_thinking_block_start_event, current_content_block_delta="", current_running_block_type=None
        )
        # Note: redacted thinking block start returns a 3-tuple instead of 4-tuple
        streaming_event, content_category, delta = result

        # Should return RedactedThinking event as single object
        assert isinstance(streaming_event, RedactedThinking)
        assert streaming_event.data == "This thinking has been redacted"
        assert content_category == ContentBlockCategory.EXTENDED_THINKING
        assert delta is None

    def test_thinking_delta_event(self, anthropic_provider: Anthropic, mock_thinking_delta_event: dict) -> None:
        """Test parsing content_block_delta event for thinking delta."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_thinking_delta_event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return ExtendedThinkingBlockDelta event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ExtendedThinkingBlockDelta)
        assert streaming_events[0].content.thinking_delta == "I need to think about this problem..."
        assert content_category == ContentBlockCategory.EXTENDED_THINKING
        assert delta is None
        assert usage is None

    def test_signature_delta_event(self, anthropic_provider: Anthropic, mock_signature_delta_event: dict) -> None:
        """Test parsing content_block_delta event for signature delta."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_signature_delta_event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return ExtendedThinkingBlockEnd event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ExtendedThinkingBlockEnd)
        assert streaming_events[0].content.signature == "signature_123"
        assert content_category == ContentBlockCategory.EXTENDED_THINKING
        assert delta is None
        assert usage is None

    # ===============================
    # TOOL USE REQUEST TESTS
    # ===============================

    def test_tool_use_block_start_event(
        self, anthropic_provider: Anthropic, mock_tool_use_block_start_event: dict
    ) -> None:
        """Test parsing content_block_start event for tool use blocks."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_tool_use_block_start_event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return ToolUseRequestStart event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ToolUseRequestStart)
        assert streaming_events[0].type == StreamingEventType.TOOL_USE_REQUEST_START
        assert streaming_events[0].content.tool_name == "test_function"
        assert streaming_events[0].content.tool_use_id == "tool_use_123"

        # Should return TOOL_USE_REQUEST category
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST
        assert delta is None
        assert usage is None

    def test_input_json_delta_event(self, anthropic_provider: Anthropic, mock_input_json_delta_event: dict) -> None:
        """Test parsing content_block_delta event for input JSON delta."""
        current_delta = ""
        result = anthropic_provider._get_parsed_stream_event(
            mock_input_json_delta_event, current_content_block_delta=current_delta, current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return ToolUseRequestDelta event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ToolUseRequestDelta)
        assert streaming_events[0].type == StreamingEventType.TOOL_USE_REQUEST_DELTA
        assert streaming_events[0].content.input_params_json_delta == '{"param": "value"'

        # Should return updated delta and TOOL_USE_REQUEST category
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST
        assert delta == '{"param": "value"'
        assert usage is None

    def test_tool_use_block_stop_event_with_delta(
        self, anthropic_provider: Anthropic, mock_tool_use_block_stop_event: dict
    ) -> None:
        """Test parsing content_block_stop event for tool use blocks with existing delta."""
        current_delta = '{"param": "value"}'
        result = anthropic_provider._get_parsed_stream_event(
            mock_tool_use_block_stop_event,
            current_content_block_delta=current_delta,
            current_running_block_type=ContentBlockCategory.TOOL_USE_REQUEST,
        )
        streaming_events, content_category, delta, usage = result

        # Should return only ToolUseRequestEnd event (no extra delta needed)
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ToolUseRequestEnd)
        assert streaming_events[0].type == StreamingEventType.TOOL_USE_REQUEST_END

        # Should return TOOL_USE_REQUEST category and reset delta
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST
        assert delta == ""
        assert usage is None

    def test_tool_use_block_stop_event_without_delta(
        self, anthropic_provider: Anthropic, mock_tool_use_block_stop_event: dict
    ) -> None:
        """Test parsing content_block_stop event for tool use blocks without existing delta."""
        current_delta = ""
        result = anthropic_provider._get_parsed_stream_event(
            mock_tool_use_block_stop_event,
            current_content_block_delta=current_delta,
            current_running_block_type=ContentBlockCategory.TOOL_USE_REQUEST,
        )
        streaming_events, content_category, delta, usage = result

        # Should return ToolUseRequestDelta with empty object and ToolUseRequestEnd
        assert len(streaming_events) == 2
        assert isinstance(streaming_events[0], ToolUseRequestDelta)
        assert streaming_events[0].content.input_params_json_delta == "{}"
        assert isinstance(streaming_events[1], ToolUseRequestEnd)
        assert streaming_events[1].type == StreamingEventType.TOOL_USE_REQUEST_END

        # Should return TOOL_USE_REQUEST category and reset delta
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST
        assert delta == ""
        assert usage is None

    # ===============================
    # TEXT BLOCK TESTS
    # ===============================

    def test_text_block_start_event(self, anthropic_provider: Anthropic, mock_text_block_start_event: dict) -> None:
        """Test parsing content_block_start event for text blocks."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_text_block_start_event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return TextBlockStart event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], TextBlockStart)
        assert streaming_events[0].type == StreamingEventType.TEXT_BLOCK_START

        # Should return TEXT_BLOCK category
        assert content_category == ContentBlockCategory.TEXT_BLOCK
        assert delta is None
        assert usage is None

    def test_text_delta_event(self, anthropic_provider: Anthropic, mock_text_delta_event: dict) -> None:
        """Test parsing content_block_delta event for text delta."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_text_delta_event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return TextBlockDelta event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], TextBlockDelta)
        assert streaming_events[0].type == StreamingEventType.TEXT_BLOCK_DELTA
        assert streaming_events[0].content.text == "Hello, world!"

        # Should return TEXT_BLOCK category
        assert content_category == ContentBlockCategory.TEXT_BLOCK
        assert delta is None
        assert usage is None

    def test_text_block_stop_event(self, anthropic_provider: Anthropic, mock_text_block_stop_event: dict) -> None:
        """Test parsing content_block_stop event for text blocks."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_text_block_stop_event,
            current_content_block_delta="",
            current_running_block_type=ContentBlockCategory.TEXT_BLOCK,
        )
        streaming_events, content_category, delta, usage = result

        # Should return TextBlockEnd event
        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], TextBlockEnd)
        assert streaming_events[0].type == StreamingEventType.TEXT_BLOCK_END

        # Should return TEXT_BLOCK category
        assert content_category == ContentBlockCategory.TEXT_BLOCK
        assert delta is None
        assert usage is None

    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================

    def test_unknown_event_type(self, anthropic_provider: Anthropic, mock_unknown_event: dict) -> None:
        """Test parsing unknown/unhandled event types."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_unknown_event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, usage = result

        # Should return empty values for unknown events
        assert streaming_events == []
        assert content_category is None
        assert delta is None
        assert usage is None

    def test_content_block_stop_with_wrong_running_type(
        self, anthropic_provider: Anthropic, mock_text_block_stop_event: dict
    ) -> None:
        """Test parsing content_block_stop with mismatched running block type."""
        result = anthropic_provider._get_parsed_stream_event(
            mock_text_block_stop_event,
            current_content_block_delta="",
            current_running_block_type=ContentBlockCategory.TOOL_USE_REQUEST,  # Wrong type
        )
        streaming_events, content_category, delta, usage = result

        # Note: The implementation handles tool_use_request stops even with text_block_stop event
        # This generates a delta and end event for tool use requests
        assert len(streaming_events) == 2
        assert isinstance(streaming_events[0], ToolUseRequestDelta)
        assert isinstance(streaming_events[1], ToolUseRequestEnd)
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST
        assert delta == ""
        assert usage is None

    # ===============================
    # PARAMETRIZED TESTS FOR COMPREHENSIVE COVERAGE
    # ===============================

    @pytest.mark.parametrize(
        "input_tokens,output_tokens,cache_read_tokens,cache_write_tokens",
        [
            (100, 50, 20, 10),  # Normal case
            (50, 25, 0, 0),  # No cached tokens
            (200, 100, 50, 25),  # Mixed caching
            (0, 0, 0, 0),  # Zero tokens
        ],
    )
    def test_usage_calculation_variations(
        self,
        anthropic_provider: Anthropic,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_write_tokens: int,
    ) -> None:
        """Test usage calculation with various token combinations."""
        event = create_message_stop_event(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens)

        result = anthropic_provider._get_parsed_stream_event(
            event, current_content_block_delta="", current_running_block_type=None
        )
        _, _, _, usage = result

        assert usage is not None
        assert usage.input == input_tokens
        assert usage.output == output_tokens
        assert usage.cache_read == cache_read_tokens
        assert usage.cache_write == cache_write_tokens

    @pytest.mark.parametrize(
        "tool_name,tool_id",
        [
            ("get_weather", "tool_abc123"),
            ("calculate_sum", "tool_xyz789"),
            ("search_database", "tool_def456"),
            ("format_text", "tool_ghi012"),
        ],
    )
    def test_tool_use_with_different_names_and_ids(
        self, anthropic_provider: Anthropic, tool_name: str, tool_id: str
    ) -> None:
        """Test tool use parsing with various tool names and IDs."""
        event = create_tool_use_start_event(tool_name, tool_id)

        result = anthropic_provider._get_parsed_stream_event(
            event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, _, _ = result

        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ToolUseRequestStart)
        assert streaming_events[0].content.tool_name == tool_name
        assert streaming_events[0].content.tool_use_id == tool_id
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST

    @pytest.mark.parametrize(
        "delta_text",
        [
            "Simple text",
            "Text with\nnewlines",
            "Text with special chars: !@#$%^&*()",
            '{"json": "data"}',
            "",  # Empty delta
            "Unicode: 🚀 ✨ 🎉",
        ],
    )
    def test_text_delta_with_various_content(self, anthropic_provider: Anthropic, delta_text: str) -> None:
        """Test text delta parsing with various content types."""
        event = create_text_delta_event(delta_text)

        result = anthropic_provider._get_parsed_stream_event(
            event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, _, _ = result

        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], TextBlockDelta)
        assert streaming_events[0].content.text == delta_text
        assert content_category == ContentBlockCategory.TEXT_BLOCK

    @pytest.mark.parametrize(
        "json_delta",
        [
            '{"param1": "value1"',
            '"param2": 123',
            ', "param3": true}',
            "",  # Empty delta
            '{"complex": {"nested": {"object": "value"}}}',
        ],
    )
    def test_input_json_delta_with_various_content(self, anthropic_provider: Anthropic, json_delta: str) -> None:
        """Test input JSON delta with various JSON fragments."""
        event = create_input_json_delta_event(json_delta)

        result = anthropic_provider._get_parsed_stream_event(
            event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, delta, _ = result

        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ToolUseRequestDelta)
        assert streaming_events[0].content.input_params_json_delta == json_delta
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST
        assert delta == json_delta

    @pytest.mark.parametrize(
        "thinking_text",
        [
            "I need to analyze this problem step by step...",
            "Let me think about the user's request...",
            "",  # Empty thinking
            "Complex thinking with\nmultiple lines\nand details",
        ],
    )
    def test_thinking_delta_with_various_content(self, anthropic_provider: Anthropic, thinking_text: str) -> None:
        """Test thinking delta parsing with various content types."""
        event = create_thinking_delta_event(thinking_text)

        result = anthropic_provider._get_parsed_stream_event(
            event, current_content_block_delta="", current_running_block_type=None
        )
        streaming_events, content_category, _, _ = result

        assert len(streaming_events) == 1
        assert isinstance(streaming_events[0], ExtendedThinkingBlockDelta)
        assert streaming_events[0].content.thinking_delta == thinking_text
        assert content_category == ContentBlockCategory.EXTENDED_THINKING

    # ===============================
    # SEQUENCE TESTING
    # ===============================

    def test_complete_text_block_sequence(self, anthropic_provider: Anthropic) -> None:
        """Test a complete sequence of text block events."""
        # Text block start event
        start_event = {"type": "content_block_start", "content_block": {"type": "text"}}
        result1 = anthropic_provider._get_parsed_stream_event(start_event, "", None)
        assert isinstance(result1[0][0], TextBlockStart)

        # Text delta events
        delta_event1 = create_text_delta_event("Hello, ")
        delta_event2 = create_text_delta_event("world!")

        result2 = anthropic_provider._get_parsed_stream_event(delta_event1, "", None)
        result3 = anthropic_provider._get_parsed_stream_event(delta_event2, "", None)

        assert isinstance(result2[0][0], TextBlockDelta)
        assert isinstance(result3[0][0], TextBlockDelta)
        assert result2[0][0].content.text == "Hello, "
        assert result3[0][0].content.text == "world!"

        # Text block stop event
        stop_event = {"type": "content_block_stop"}
        result4 = anthropic_provider._get_parsed_stream_event(stop_event, "", ContentBlockCategory.TEXT_BLOCK)
        assert isinstance(result4[0][0], TextBlockEnd)

    def test_complete_tool_use_sequence(self, anthropic_provider: Anthropic) -> None:
        """Test a complete sequence of tool use events."""
        # Tool use start
        start_event = create_tool_use_start_event("test_func", "tool_123")
        result1 = anthropic_provider._get_parsed_stream_event(start_event, "", None)
        assert isinstance(result1[0][0], ToolUseRequestStart)

        # JSON input delta
        delta_event = create_input_json_delta_event('{"param": "value"}')
        result2 = anthropic_provider._get_parsed_stream_event(delta_event, "", None)
        assert isinstance(result2[0][0], ToolUseRequestDelta)

        # Tool use stop
        stop_event = {"type": "content_block_stop"}
        result3 = anthropic_provider._get_parsed_stream_event(
            stop_event, '{"param": "value"}', ContentBlockCategory.TOOL_USE_REQUEST
        )
        assert isinstance(result3[0][0], ToolUseRequestEnd)

    def test_complete_thinking_sequence(self, anthropic_provider: Anthropic) -> None:
        """Test a complete sequence of thinking events."""
        # Thinking start
        start_event = {"type": "content_block_start", "content_block": {"type": "thinking"}}
        result1 = anthropic_provider._get_parsed_stream_event(start_event, "", None)
        # Thinking start returns single object in 3-tuple
        assert isinstance(result1[0], ExtendedThinkingBlockStart)

        # Thinking delta
        delta_event = create_thinking_delta_event("Let me think...")
        result2 = anthropic_provider._get_parsed_stream_event(delta_event, "", None)
        assert isinstance(result2[0][0], ExtendedThinkingBlockDelta)

        # Signature (end of thinking)
        signature_event = {"type": "content_block_delta", "delta": {"type": "signature_delta", "signature": "sig_123"}}
        result3 = anthropic_provider._get_parsed_stream_event(signature_event, "", None)
        assert isinstance(result3[0][0], ExtendedThinkingBlockEnd)

    # ===============================
    # TYPE SAFETY TESTS
    # ===============================

    def test_return_type_consistency(self, anthropic_provider: Anthropic, mock_message_stop_event: dict) -> None:
        """Test that return types are always consistent with the function signature."""
        result = anthropic_provider._get_parsed_stream_event(mock_message_stop_event, "", None)

        # Should always return a 4-tuple
        assert isinstance(result, tuple)
        assert len(result) == 4

        streaming_events, content_category, delta, usage = result

        # Each element should be of correct type or None
        assert isinstance(streaming_events, list)
        assert all(isinstance(event, StreamingEvent) for event in streaming_events)
        assert content_category is None or isinstance(content_category, ContentBlockCategory)
        assert delta is None or isinstance(delta, str)
        assert usage is None or isinstance(usage, LLMUsage)

    def test_all_streaming_event_types_are_properly_typed(self, anthropic_provider: Anthropic) -> None:
        """Test that all returned StreamingEvent objects have proper types."""
        # Test each event type that returns a StreamingEvent
        test_cases = [
            # Text block start
            ({"type": "content_block_start", "content_block": {"type": "text"}}, TextBlockStart),
            # Text block delta
            ({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "test"}}, TextBlockDelta),
            # Text block end
            ({"type": "content_block_stop"}, TextBlockEnd),
            # Tool use start
            (
                {"type": "content_block_start", "content_block": {"type": "tool_use", "name": "test", "id": "123"}},
                ToolUseRequestStart,
            ),
            # Tool use delta
            (
                {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "{}"}},
                ToolUseRequestDelta,
            ),
            # Tool use end
            ({"type": "content_block_stop"}, ToolUseRequestEnd),
            # Thinking start
            ({"type": "content_block_start", "content_block": {"type": "thinking"}}, ExtendedThinkingBlockStart),
            # Thinking delta
            (
                {"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": "test"}},
                ExtendedThinkingBlockDelta,
            ),
        ]

        for event_data, expected_type in test_cases:
            # Special handling for content_block_stop events
            running_type = None
            if event_data["type"] == "content_block_stop":
                if expected_type == TextBlockEnd:
                    running_type = ContentBlockCategory.TEXT_BLOCK
                elif expected_type == ToolUseRequestEnd:
                    running_type = ContentBlockCategory.TOOL_USE_REQUEST

            result = anthropic_provider._get_parsed_stream_event(event_data, "", running_type)
            streaming_events = result[0]

            # Handle different return patterns
            if expected_type == ExtendedThinkingBlockStart:
                # Special case: thinking start returns single object in 3-tuple
                assert isinstance(streaming_events, expected_type)
            elif streaming_events:  # Some events might return empty list
                # For tool use end without delta, we get 2 events
                if expected_type == ToolUseRequestEnd and len(streaming_events) == 2:
                    assert isinstance(streaming_events[1], expected_type)
                else:
                    assert len(streaming_events) >= 1
                    assert isinstance(streaming_events[0], expected_type)
                    assert hasattr(streaming_events[0], "type")
                    assert isinstance(streaming_events[0].type, StreamingEventType)
