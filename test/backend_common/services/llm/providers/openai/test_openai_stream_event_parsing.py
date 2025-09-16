"""
Tests for OpenAI LLM Provider Stream Event Parsing.

This module comprehensively tests the OpenAI._get_parsed_stream_event method,
which is responsible for parsing various types of OpenAI stream events into
our internal streaming event format.

Test Categories:
- Response completion events (with/without usage)
- Function/tool call events (start, delta, end)
- Text block events (start, delta, end)
- Edge cases and error handling
- Parametrized tests for various input combinations
- Sequence testing for complete event flows
- Type safety validation
"""

from typing import Optional, Tuple
from unittest.mock import MagicMock

import pytest

# ConfigManager is automatically initialized by conftest.py fixture
from app.backend_common.models.dto.message_thread_dto import ContentBlockCategory
from app.backend_common.services.llm.dataclasses.main import (
    LLMUsage,
    StreamingEvent,
    StreamingEventType,
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)
from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI

# Import fixtures from organized fixture modules
from test.fixtures.openai import (
    create_function_arguments_delta_event,
    create_function_call_added_event,
    create_text_delta_event,
    create_usage_event,
)

# Use provider fixture that handles import properly


class TestOpenAIStreamEventParsing:
    """Test suite for OpenAI stream event parsing functionality."""

    # ===============================
    # RESPONSE COMPLETION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_response_completed_with_usage(
        self, openai_provider, mock_response_completed_event: MagicMock
    ) -> None:
        """Test parsing response.completed event with usage information."""
        result: Tuple[
            Optional[StreamingEvent], Optional[ContentBlockCategory], Optional[LLMUsage]
        ] = await openai_provider._get_parsed_stream_event(mock_response_completed_event)

        streaming_event, content_category, usage = result

        # Should return None for streaming event and content category
        assert streaming_event is None
        assert content_category is None

        # Should return usage information
        assert usage is not None
        assert isinstance(usage, LLMUsage)
        assert usage.input == 80  # 100 - 20 (cached)
        assert usage.output == 50
        assert usage.cache_read == 20
        assert usage.cache_write is None

    @pytest.mark.asyncio
    async def test_response_completed_without_usage(
        self, openai_provider, mock_response_completed_without_usage: MagicMock
    ) -> None:
        """Test parsing response.completed event without usage information."""
        result = await openai_provider._get_parsed_stream_event(mock_response_completed_without_usage)
        streaming_event, content_category, usage = result

        # Should return None for all fields when no usage data
        assert streaming_event is None
        assert content_category is None
        assert usage is None

    @pytest.mark.asyncio
    async def test_response_completed_with_missing_usage_fields(
        self, openai_provider: OpenAI, mock_response_completed_incomplete_usage: MagicMock
    ) -> None:
        """Test parsing response.completed with incomplete usage data."""
        # This should raise an AttributeError
        with pytest.raises(AttributeError):
            await openai_provider._get_parsed_stream_event(mock_response_completed_incomplete_usage)

    # ===============================
    # FUNCTION CALL TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_function_call_added_event(
        self, openai_provider: OpenAI, mock_function_call_added_event: MagicMock
    ) -> None:
        """Test parsing response.output_item.added event for function calls."""
        result = await openai_provider._get_parsed_stream_event(mock_function_call_added_event)
        streaming_event, content_category, usage = result

        # Should return ToolUseRequestStart event
        assert streaming_event is not None
        assert isinstance(streaming_event, ToolUseRequestStart)
        assert streaming_event.type == StreamingEventType.TOOL_USE_REQUEST_START
        assert streaming_event.content.tool_name == "test_function"
        assert streaming_event.content.tool_use_id == "call_123456"

        # Should return TOOL_USE_REQUEST category
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST

        # Should return None for usage
        assert usage is None

    @pytest.mark.asyncio
    async def test_function_arguments_delta_event(
        self, openai_provider: OpenAI, mock_function_arguments_delta_event: MagicMock
    ) -> None:
        """Test parsing response.function_call_arguments.delta event."""
        result = await openai_provider._get_parsed_stream_event(mock_function_arguments_delta_event)
        streaming_event, content_category, usage = result

        # Should return ToolUseRequestDelta event
        assert streaming_event is not None
        assert isinstance(streaming_event, ToolUseRequestDelta)
        assert streaming_event.type == StreamingEventType.TOOL_USE_REQUEST_DELTA
        assert streaming_event.content.input_params_json_delta == '{"param": "value'

        # Should return TOOL_USE_REQUEST category
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST

        # Should return None for usage
        assert usage is None

    @pytest.mark.asyncio
    async def test_function_arguments_done_event(
        self, openai_provider: OpenAI, mock_function_arguments_done_event: MagicMock
    ) -> None:
        """Test parsing response.function_call_arguments.done event."""
        result = await openai_provider._get_parsed_stream_event(mock_function_arguments_done_event)
        streaming_event, content_category, usage = result

        # Should return ToolUseRequestEnd event
        assert streaming_event is not None
        assert isinstance(streaming_event, ToolUseRequestEnd)
        assert streaming_event.type == StreamingEventType.TOOL_USE_REQUEST_END

        # Should return TOOL_USE_REQUEST category
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST

        # Should return None for usage
        assert usage is None

    # ===============================
    # MESSAGE/TEXT BLOCK TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_message_added_event(self, openai_provider: OpenAI, mock_message_added_event: MagicMock) -> None:
        """Test parsing response.output_item.added event for messages."""
        result = await openai_provider._get_parsed_stream_event(mock_message_added_event)
        streaming_event, content_category, usage = result

        # Should return TextBlockStart event
        assert streaming_event is not None
        assert isinstance(streaming_event, TextBlockStart)
        assert streaming_event.type == StreamingEventType.TEXT_BLOCK_START

        # Should return TEXT_BLOCK category
        assert content_category == ContentBlockCategory.TEXT_BLOCK

        # Should return None for usage
        assert usage is None

    @pytest.mark.asyncio
    async def test_output_text_delta_event(
        self, openai_provider: OpenAI, mock_output_text_delta_event: MagicMock
    ) -> None:
        """Test parsing response.output_text.delta event."""
        result = await openai_provider._get_parsed_stream_event(mock_output_text_delta_event)
        streaming_event, content_category, usage = result

        # Should return TextBlockDelta event
        assert streaming_event is not None
        assert isinstance(streaming_event, TextBlockDelta)
        assert streaming_event.type == StreamingEventType.TEXT_BLOCK_DELTA
        assert streaming_event.content.text == "Hello, world!"

        # Should return TEXT_BLOCK category
        assert content_category == ContentBlockCategory.TEXT_BLOCK

        # Should return None for usage
        assert usage is None

    @pytest.mark.asyncio
    async def test_output_text_done_event(
        self, openai_provider: OpenAI, mock_output_text_done_event: MagicMock
    ) -> None:
        """Test parsing response.output_text.done event."""
        result = await openai_provider._get_parsed_stream_event(mock_output_text_done_event)
        streaming_event, content_category, usage = result

        # Should return TextBlockEnd event
        assert streaming_event is not None
        assert isinstance(streaming_event, TextBlockEnd)
        assert streaming_event.type == StreamingEventType.TEXT_BLOCK_END

        # Should return TEXT_BLOCK category
        assert content_category == ContentBlockCategory.TEXT_BLOCK

        # Should return None for usage
        assert usage is None

    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================

    @pytest.mark.asyncio
    async def test_unknown_event_type(self, openai_provider: OpenAI, mock_unknown_event: MagicMock) -> None:
        """Test parsing unknown/unhandled event types."""
        result = await openai_provider._get_parsed_stream_event(mock_unknown_event)
        streaming_event, content_category, usage = result

        # Should return None for all values
        assert streaming_event is None
        assert content_category is None
        assert usage is None

    @pytest.mark.asyncio
    async def test_output_item_added_with_unknown_item_type(
        self, openai_provider: OpenAI, mock_output_item_added_unknown_type: MagicMock
    ) -> None:
        """Test parsing output_item.added with unknown item type."""
        result = await openai_provider._get_parsed_stream_event(mock_output_item_added_unknown_type)
        streaming_event, content_category, usage = result

        # Should return None for all values
        assert streaming_event is None
        assert content_category is None
        assert usage is None

    # ===============================
    # PARAMETRIZED TESTS FOR COMPREHENSIVE COVERAGE
    # ===============================

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_tokens,output_tokens,cached_tokens,expected_input",
        [
            (100, 50, 20, 80),  # Normal case
            (50, 25, 0, 50),  # No cached tokens
            (200, 100, 200, 0),  # All tokens cached
            (150, 75, 50, 100),  # Partial caching
        ],
    )
    async def test_usage_calculation_variations(
        self, openai_provider: OpenAI, input_tokens: int, output_tokens: int, cached_tokens: int, expected_input: int
    ) -> None:
        """Test usage calculation with various token combinations."""
        event = create_usage_event(input_tokens, output_tokens, cached_tokens)

        result = await openai_provider._get_parsed_stream_event(event)
        _, _, usage = result

        assert usage is not None
        assert usage.input == expected_input
        assert usage.output == output_tokens
        assert usage.cache_read == cached_tokens

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name,call_id",
        [
            ("get_weather", "call_abc123"),
            ("calculate_sum", "call_xyz789"),
            ("search_database", "call_def456"),
            ("format_text", "call_ghi012"),
        ],
    )
    async def test_function_call_with_different_names_and_ids(
        self, openai_provider: OpenAI, tool_name: str, call_id: str
    ) -> None:
        """Test function call parsing with various tool names and call IDs."""
        event = create_function_call_added_event(tool_name, call_id)

        result = await openai_provider._get_parsed_stream_event(event)
        streaming_event, content_category, usage = result

        assert isinstance(streaming_event, ToolUseRequestStart)
        assert streaming_event.content.tool_name == tool_name
        assert streaming_event.content.tool_use_id == call_id
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST

    @pytest.mark.asyncio
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
    async def test_text_delta_with_various_content(self, openai_provider: OpenAI, delta_text: str) -> None:
        """Test text delta parsing with various content types."""
        event = create_text_delta_event(delta_text)

        result = await openai_provider._get_parsed_stream_event(event)
        streaming_event, content_category, usage = result

        assert isinstance(streaming_event, TextBlockDelta)
        assert streaming_event.content.text == delta_text
        assert content_category == ContentBlockCategory.TEXT_BLOCK

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "function_args_delta",
        [
            '{"param1": "value1"',
            '"param2": 123',
            ', "param3": true}',
            "",  # Empty delta
            '{"complex": {"nested": {"object": "value"}}}',
        ],
    )
    async def test_function_arguments_delta_with_various_json(
        self, openai_provider: OpenAI, function_args_delta: str
    ) -> None:
        """Test function arguments delta with various JSON fragments."""
        event = create_function_arguments_delta_event(function_args_delta)

        result = await openai_provider._get_parsed_stream_event(event)
        streaming_event, content_category, usage = result

        assert isinstance(streaming_event, ToolUseRequestDelta)
        assert streaming_event.content.input_params_json_delta == function_args_delta
        assert content_category == ContentBlockCategory.TOOL_USE_REQUEST

    # ===============================
    # SEQUENCE TESTING
    # ===============================

    @pytest.mark.asyncio
    async def test_complete_text_block_sequence(self, openai_provider: OpenAI) -> None:
        """Test a complete sequence of text block events."""
        # Message added event
        message_event = MagicMock()
        message_event.type = "response.output_item.added"
        message_event.item = MagicMock()
        message_event.item.type = "message"

        result1 = await openai_provider._get_parsed_stream_event(message_event)
        assert isinstance(result1[0], TextBlockStart)

        # Text delta events
        delta_event1 = create_text_delta_event("Hello, ")
        delta_event2 = create_text_delta_event("world!")

        result2 = await openai_provider._get_parsed_stream_event(delta_event1)
        result3 = await openai_provider._get_parsed_stream_event(delta_event2)

        assert isinstance(result2[0], TextBlockDelta)
        assert isinstance(result3[0], TextBlockDelta)
        assert result2[0].content.text == "Hello, "
        assert result3[0].content.text == "world!"

        # Text done event
        done_event = MagicMock()
        done_event.type = "response.output_text.done"

        result4 = await openai_provider._get_parsed_stream_event(done_event)
        assert isinstance(result4[0], TextBlockEnd)

    @pytest.mark.asyncio
    async def test_complete_function_call_sequence(self, openai_provider: OpenAI) -> None:
        """Test a complete sequence of function call events."""
        # Function call added
        call_added = create_function_call_added_event("test_func", "call_123")
        result1 = await openai_provider._get_parsed_stream_event(call_added)
        assert isinstance(result1[0], ToolUseRequestStart)

        # Arguments delta
        args_delta = create_function_arguments_delta_event('{"param": "value"}')
        result2 = await openai_provider._get_parsed_stream_event(args_delta)
        assert isinstance(result2[0], ToolUseRequestDelta)

        # Arguments done
        args_done = MagicMock()
        args_done.type = "response.function_call_arguments.done"
        result3 = await openai_provider._get_parsed_stream_event(args_done)
        assert isinstance(result3[0], ToolUseRequestEnd)

    # ===============================
    # TYPE SAFETY TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_return_type_consistency(
        self, openai_provider: OpenAI, mock_response_completed_event: MagicMock
    ) -> None:
        """Test that return types are always consistent with the function signature."""
        result = await openai_provider._get_parsed_stream_event(mock_response_completed_event)

        # Should always return a 3-tuple
        assert isinstance(result, tuple)
        assert len(result) == 3

        streaming_event, content_category, usage = result

        # Each element should be of correct type or None
        assert streaming_event is None or isinstance(streaming_event, StreamingEvent)
        assert content_category is None or isinstance(content_category, ContentBlockCategory)
        assert usage is None or isinstance(usage, LLMUsage)

    @pytest.mark.asyncio
    async def test_all_streaming_event_types_are_properly_typed(self, openai_provider: OpenAI) -> None:
        """Test that all returned StreamingEvent objects have proper types."""
        # Test each event type that returns a StreamingEvent
        test_cases = [
            # Text block start
            (
                lambda: (
                    event := MagicMock(),
                    setattr(event, "type", "response.output_item.added"),
                    setattr(event, "item", MagicMock()),
                    setattr(event.item, "type", "message"),
                    event,
                )[-1],
                TextBlockStart,
            ),
            # Text block delta
            (
                lambda: (
                    event := MagicMock(),
                    setattr(event, "type", "response.output_text.delta"),
                    setattr(event, "delta", "test"),
                    event,
                )[-1],
                TextBlockDelta,
            ),
            # Text block end
            (
                lambda: (event := MagicMock(), setattr(event, "type", "response.output_text.done"), event)[-1],
                TextBlockEnd,
            ),
            # Tool use start
            (
                lambda: (
                    event := MagicMock(),
                    setattr(event, "type", "response.output_item.added"),
                    setattr(event, "item", MagicMock()),
                    setattr(event.item, "type", "function_call"),
                    setattr(event.item, "name", "test"),
                    setattr(event.item, "call_id", "call_123"),
                    event,
                )[-1],
                ToolUseRequestStart,
            ),
            # Tool use delta
            (
                lambda: (
                    event := MagicMock(),
                    setattr(event, "type", "response.function_call_arguments.delta"),
                    setattr(event, "delta", "{}"),
                    event,
                )[-1],
                ToolUseRequestDelta,
            ),
            # Tool use end
            (
                lambda: (event := MagicMock(), setattr(event, "type", "response.function_call_arguments.done"), event)[
                    -1
                ],
                ToolUseRequestEnd,
            ),
        ]

        for event_factory, expected_type in test_cases:
            event = event_factory()
            result = await openai_provider._get_parsed_stream_event(event)
            streaming_event = result[0]

            assert streaming_event is not None
            assert isinstance(streaming_event, expected_type)
            assert hasattr(streaming_event, "type")
            assert isinstance(streaming_event.type, StreamingEventType)
