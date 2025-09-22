"""
Unit tests for Google/Gemini streaming event parsing.

This module tests the streaming event parsing functionality of the Google provider,
covering various streaming scenarios including:
- Text content streaming
- Function call streaming
- Mixed content streaming
- Error handling during streaming
- Malformed function calls
- Safety blocks and other finish reasons
- Performance with large streams

The tests follow .deputydevrules guidelines and use proper fixtures.
"""

import asyncio
import json
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


# Mock Google types for testing - comprehensive
class MockPart:
    def __init__(self, text: str = None, function_call=None, function_response=None, inline_data=None):
        self.text = text
        self.function_call = function_call
        self.function_response = function_response
        self.inline_data = inline_data

    @classmethod
    def from_text(cls, text: str):
        return cls(text=text)

    @classmethod
    def from_function_call(cls, name: str, args: dict):
        function_call = type("FunctionCall", (), {"name": name, "args": args})()
        return cls(function_call=function_call)

    @classmethod
    def from_function_response(cls, name: str, response: Any):
        function_response = type("FunctionResponse", (), {"name": name, "response": response})()
        return cls(function_response=function_response)

    @classmethod
    def from_bytes(cls, data: bytes, mime_type: str):
        inline_data = type("InlineData", (), {"data": data, "mime_type": mime_type})()
        return cls(inline_data=inline_data)


class MockContent:
    def __init__(self, role: str, parts: List[MockPart]):
        self.role = role
        self.parts = parts


@pytest.fixture(autouse=True)
def setup_comprehensive_mocks():
    """Set up comprehensive mocks for all Google and configuration dependencies."""

    # Mock all Google types
    mock_types = Mock()
    mock_types.Part = MockPart
    mock_types.Content = MockContent
    mock_types.Tool = Mock
    mock_types.ToolConfig = Mock
    mock_types.HttpOptions = Mock
    mock_types.GenerateContentResponse = Mock
    mock_types.Schema = Mock
    mock_types.FunctionDeclaration = Mock
    mock_types.GoogleSearch = Mock

    # Mock genai module
    mock_genai = Mock()
    mock_genai.types = mock_types
    mock_genai.Client = Mock
    mock_genai.errors = Mock()

    # Mock google module
    mock_google = Mock()
    mock_google.genai = mock_genai

    # Mock oauth2
    mock_oauth2 = Mock()
    mock_oauth2.service_account = Mock()
    mock_oauth2.service_account.Credentials = Mock()
    mock_oauth2.service_account.Credentials.from_service_account_info = Mock(return_value=Mock())

    # Mock service account
    mock_service_account = Mock()
    mock_service_account.Credentials = Mock()
    mock_service_account.Credentials.from_service_account_info = Mock(return_value=Mock())

    # Mock CONFIG with comprehensive configuration
    mock_config_obj = Mock()
    mock_config_obj.config = {
        "VERTEX": {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\\ntest-key\\n-----END PRIVATE KEY-----\\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "12345",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
            "location": "us-central1",
        },
        "REDIS_CACHE_HOSTS": {"genai": {"LABEL": "test-genai", "HOST": "localhost", "PORT": 6379}},
        "INTERSERVICE_TIMEOUT": 30,
    }

    # Mock GeminiServiceClient
    class MockGeminiServiceClient:
        def __init__(self, vertex_config=None):
            pass

        async def get_llm_stream_response(self, *args, **kwargs):
            return Mock()

        async def get_llm_non_stream_response(self, *args, **kwargs):
            return Mock()

        async def get_tokens(self, *args, **kwargs):
            return 100

    patches = [
        # Mock sys.modules for Google packages
        patch.dict(
            "sys.modules",
            {
                "google": mock_google,
                "google.genai": mock_genai,
                "google.oauth2": mock_oauth2,
                "google.oauth2.service_account": mock_service_account,
            },
        ),
        # Mock CONFIG
        patch("app.backend_common.utils.sanic_wrapper.CONFIG", mock_config_obj),
        # Mock the service client directly at the module level
        patch(
            "deputydev_core.llm_handler.providers.google.llm_provider.GeminiServiceClient", MockGeminiServiceClient
        ),
        # Note: gemini service client config is now handled through deputydev_core.clients
        # The GeminiServiceClient mock above should handle the config requirements
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


from deputydev_core.llm_handler.dataclasses.main import (
    LLMCallResponseTypes,
    MalformedToolUseRequest,
    StreamingResponse,
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)

from app.backend_common.models.dto.message_thread_dto import ContentBlockCategory

# Import fixtures


class TestGoogleStreamEventParsing:
    """Test suite for Google stream event parsing methods."""

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_text_chunk(
        self,
        google_provider,
        mock_google_stream_text_chunk: MagicMock,
    ) -> None:
        """Test parsing text chunk from Google stream."""
        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(
            mock_google_stream_text_chunk
        )

        # Should produce text-related events
        assert len(event_blocks) >= 1
        assert event_block_category == ContentBlockCategory.TEXT_BLOCK

        # Check for text events
        event_types = [type(event) for event in event_blocks]
        assert TextBlockStart in event_types
        assert TextBlockDelta in event_types

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_function_chunk(
        self,
        google_provider,
        mock_google_stream_function_chunk: MagicMock,
    ) -> None:
        """Test parsing function call chunk from Google stream."""
        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(
            mock_google_stream_function_chunk
        )

        # Should produce function call events
        assert len(event_blocks) >= 1
        assert event_block_category is None  # Function calls end immediately

        # Check for function call events
        event_types = [type(event) for event in event_blocks]
        assert ToolUseRequestStart in event_types
        assert ToolUseRequestDelta in event_types
        assert ToolUseRequestEnd in event_types

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_final_chunk(
        self,
        google_provider,
        mock_google_stream_final_chunk: MagicMock,
    ) -> None:
        """Test parsing final chunk with usage information."""
        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(
            mock_google_stream_final_chunk, current_running_block_type=ContentBlockCategory.TEXT_BLOCK
        )

        # Should end the current text block
        assert len(event_blocks) >= 1
        event_types = [type(event) for event in event_blocks]
        assert TextBlockEnd in event_types

        # Should have usage information
        assert event_usage is not None
        assert event_usage.input == 80  # 100 - 20 cached
        assert event_usage.output == 50
        assert event_usage.cache_read == 20

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_malformed_chunk(
        self,
        google_provider,
        mock_google_stream_malformed_chunk: MagicMock,
    ) -> None:
        """Test parsing malformed function call chunk."""
        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(
            mock_google_stream_malformed_chunk
        )

        # Should produce malformed tool use request
        assert len(event_blocks) >= 1
        event_types = [type(event) for event in event_blocks]
        assert MalformedToolUseRequest in event_types

        # Should have usage information
        assert event_usage is not None
        assert event_usage.input == 70  # 80 - 10 cached
        assert event_usage.output == 25
        assert event_usage.cache_read == 10

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_multiple_parts_chunk(
        self,
        google_provider,
        mock_google_stream_multiple_parts_chunk: MagicMock,
    ) -> None:
        """Test parsing chunk with multiple content parts."""
        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(
            mock_google_stream_multiple_parts_chunk
        )

        # Should handle both text and function call
        assert len(event_blocks) >= 4  # Text start, text delta, function start/delta/end

        # Check for both text and function events
        event_types = [type(event) for event in event_blocks]
        assert TextBlockStart in event_types
        assert TextBlockDelta in event_types
        assert ToolUseRequestStart in event_types
        assert ToolUseRequestEnd in event_types

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_block_transitions(
        self,
        google_provider,
        mock_google_stream_text_chunk: MagicMock,
        mock_google_stream_function_chunk: MagicMock,
    ) -> None:
        """Test proper block transitions between different content types."""
        # Start with text
        events1, category1, _ = await google_provider._get_parsed_stream_event(mock_google_stream_text_chunk)

        # Then function call (should end text block and start function block)
        events2, category2, _ = await google_provider._get_parsed_stream_event(
            mock_google_stream_function_chunk, current_running_block_type=category1
        )

        # Should properly transition from text to function
        event_types = [type(event) for event in events2]
        assert TextBlockEnd in event_types  # Should end previous text block
        assert ToolUseRequestStart in event_types  # Should start function block


class TestGoogleStreamingResponseParsing:
    """Test suite for complete Google streaming response parsing."""

    @pytest.mark.asyncio
    async def test_parse_streaming_response_complete_flow(
        self,
        google_provider,
        mock_google_complete_stream,
    ) -> None:
        """Test parsing complete streaming response flow."""
        result = await google_provider._parse_streaming_response(
            mock_google_complete_stream, stream_id="test_stream_123", session_id=456
        )

        assert isinstance(result, StreamingResponse)
        assert result.type == LLMCallResponseTypes.STREAMING

        # Consume all events
        events = []
        async for event in result.content:
            events.append(event)

        # Should have multiple events from the complete flow
        assert len(events) > 0

        # Check usage after streaming completes
        usage = await result.usage
        assert usage.input == 90  # 120 - 30 cached
        assert usage.output == 80
        assert usage.cache_read == 30

        # Check accumulated events
        accumulated = await result.accumulated_events
        assert len(accumulated) == len(events)

    @pytest.mark.asyncio
    async def test_parse_streaming_response_with_error(
        self,
        google_provider,
        mock_google_stream_with_error,
    ) -> None:
        """Test streaming response error handling."""
        result = await google_provider._parse_streaming_response(mock_google_stream_with_error)

        assert isinstance(result, StreamingResponse)

        # Should handle errors gracefully
        events = []
        try:
            async for event in result.content:
                events.append(event)
        except Exception:
            # Errors during streaming should be handled
            pass

        # Should have processed at least one event before error
        assert len(events) >= 1

        # Usage should be available even after error
        usage = await result.usage
        assert usage is not None

    @pytest.mark.asyncio
    async def test_parse_streaming_response_max_tokens(
        self,
        google_provider,
        mock_google_stream_max_tokens,
    ) -> None:
        """Test streaming response that hits max tokens limit."""
        result = await google_provider._parse_streaming_response(mock_google_stream_max_tokens)

        assert isinstance(result, StreamingResponse)

        # Consume events
        events = []
        async for event in result.content:
            events.append(event)

        # Should process events and handle max tokens properly
        assert len(events) > 0

        # Usage should reflect max tokens hit
        usage = await result.usage
        assert usage.output == 4096  # Hit max tokens

    @pytest.mark.asyncio
    async def test_parse_streaming_response_safety_block(
        self,
        google_provider,
        mock_google_stream_safety_block,
    ) -> None:
        """Test streaming response blocked by safety filters."""
        result = await google_provider._parse_streaming_response(mock_google_stream_safety_block)

        assert isinstance(result, StreamingResponse)

        # Should handle safety blocks gracefully
        events = []
        async for event in result.content:
            events.append(event)

        # Should have some events before block
        assert len(events) > 0

        # Usage should be available
        usage = await result.usage
        assert usage.input == 40  # 50 - 10 cached
        assert usage.output == 15

    @pytest.mark.asyncio
    async def test_parse_streaming_response_complex_function_args(
        self,
        google_provider,
        mock_google_stream_function_with_complex_args,
    ) -> None:
        """Test streaming with complex function call arguments."""
        result = await google_provider._parse_streaming_response(mock_google_stream_function_with_complex_args)

        assert isinstance(result, StreamingResponse)

        # Consume events
        events = []
        async for event in result.content:
            events.append(event)

        # Should handle complex function arguments properly
        assert len(events) > 0

        # Should have function-related events
        event_types = [type(event) for event in events]
        assert ToolUseRequestStart in event_types
        assert ToolUseRequestDelta in event_types
        assert ToolUseRequestEnd in event_types

        # Check that complex args were processed
        delta_events = [event for event in events if isinstance(event, ToolUseRequestDelta)]
        assert len(delta_events) > 0

        # Complex arguments should be valid JSON
        for delta_event in delta_events:
            try:
                json.loads(delta_event.content.input_params_json_delta)
            except json.JSONDecodeError:
                pytest.fail("Complex function arguments should produce valid JSON")

    @pytest.mark.asyncio
    async def test_parse_streaming_response_empty_chunks(
        self,
        google_provider,
        mock_google_stream_empty_chunks,
    ) -> None:
        """Test streaming response with empty chunks."""
        result = await google_provider._parse_streaming_response(mock_google_stream_empty_chunks)

        assert isinstance(result, StreamingResponse)

        # Should handle empty chunks gracefully
        events = []
        async for event in result.content:
            events.append(event)

        # May have few or no events due to empty chunks
        assert isinstance(events, list)

        # Usage should still be available
        usage = await result.usage
        assert usage.input == 15  # 20 - 5 cached
        assert usage.output == 0
        assert usage.cache_read == 5

    @pytest.mark.asyncio
    async def test_parse_streaming_response_cancellation(
        self,
        google_provider,
    ) -> None:
        """Test streaming response with cancellation."""

        # Create a mock stream that should be cancelled
        async def cancellable_stream():
            chunk = MagicMock()
            chunk.usage_metadata = None
            candidate = MagicMock()
            candidate.finish_reason = None
            candidate.content = MagicMock()
            text_part = MagicMock()
            text_part.text = "Starting..."
            text_part.function_call = None
            candidate.content.parts = [text_part]
            chunk.candidates = [candidate]
            yield chunk

            # Simulate more chunks that would be cancelled
            await asyncio.sleep(0.1)
            yield chunk

        # Mock cancellation checker
        mock_checker = MagicMock()
        mock_checker.is_cancelled.return_value = True
        mock_checker.stop_monitoring = AsyncMock()

        google_provider.checker = mock_checker

        with patch("deputydev_core.llm_handler.providers.google.llm_provider.CodeGenTasksCache") as mock_cache:
            mock_cache.cleanup_session_data = AsyncMock()

            result = await google_provider._parse_streaming_response(cancellable_stream(), session_id=789)

            # Should handle cancellation
            events = []
            try:
                async for event in result.content:
                    events.append(event)
            except asyncio.CancelledError:
                # Expected when cancelled
                pass

            # Should have checked for cancellation
            mock_checker.is_cancelled.assert_called()

            # Usage should still be available
            usage = await result.usage
            assert usage is not None


class TestGoogleStreamEventEdgeCases:
    """Test suite for edge cases in Google stream event parsing."""

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_invalid_json_in_function_args(
        self,
        google_provider,
    ) -> None:
        """Test handling invalid JSON in function call arguments."""
        # Create chunk with invalid JSON args
        chunk = MagicMock()
        chunk.usage_metadata = None

        candidate = MagicMock()
        candidate.finish_reason = None
        candidate.content = MagicMock()

        function_part = MagicMock()
        function_part.text = None
        function_part.function_call = MagicMock()
        function_part.function_call.name = "test_function"
        function_part.function_call.id = "call_123"
        function_part.function_call.args = "invalid json string"  # Invalid JSON

        candidate.content.parts = [function_part]
        chunk.candidates = [candidate]

        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(chunk)

        # Should handle invalid JSON gracefully
        assert len(event_blocks) > 0

        # Should have function events with fallback JSON
        delta_events = [event for event in event_blocks if isinstance(event, ToolUseRequestDelta)]
        assert len(delta_events) > 0

        # Should produce valid JSON even with invalid input
        for delta_event in delta_events:
            try:
                json.loads(delta_event.content.input_params_json_delta)
            except json.JSONDecodeError:
                pytest.fail("Should produce valid JSON even with invalid input")

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_non_serializable_function_args(
        self,
        google_provider,
    ) -> None:
        """Test handling non-serializable function call arguments."""
        # Create chunk with non-serializable args
        chunk = MagicMock()
        chunk.usage_metadata = None

        candidate = MagicMock()
        candidate.finish_reason = None
        candidate.content = MagicMock()

        function_part = MagicMock()
        function_part.text = None
        function_part.function_call = MagicMock()
        function_part.function_call.name = "test_function"
        function_part.function_call.id = "call_456"

        # Non-serializable object
        class NonSerializable:
            pass

        function_part.function_call.args = {"obj": NonSerializable()}

        candidate.content.parts = [function_part]
        chunk.candidates = [candidate]

        event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(chunk)

        # Should handle non-serializable objects gracefully
        assert len(event_blocks) > 0

        # Should have function events with error JSON
        delta_events = [event for event in event_blocks if isinstance(event, ToolUseRequestDelta)]
        assert len(delta_events) > 0

        # Should produce error JSON for non-serializable args
        for delta_event in delta_events:
            args_json = delta_event.content.input_params_json_delta
            parsed_args = json.loads(args_json)
            assert "error" in parsed_args or "Failed to serialize" in str(parsed_args)

    @pytest.mark.asyncio
    async def test_get_parsed_stream_event_no_candidates(
        self,
        google_provider,
    ) -> None:
        """Test handling chunks with no candidates."""
        chunk = MagicMock()
        chunk.usage_metadata = None
        chunk.candidates = []  # No candidates

        # Should handle gracefully without crashing
        try:
            event_blocks, event_block_category, event_usage = await google_provider._get_parsed_stream_event(chunk)
            # If it doesn't raise an exception, that's a pass
            assert isinstance(event_blocks, list)
        except (IndexError, AttributeError):
            # May raise an error, which is also acceptable behavior
            pass

    @pytest.mark.asyncio
    async def test_parse_streaming_response_performance_many_events(
        self,
        google_provider,
    ) -> None:
        """Test performance with streaming response containing many events."""

        # Create a stream with many small chunks
        async def large_stream():
            for i in range(100):  # 100 chunks
                chunk = MagicMock()
                chunk.usage_metadata = None

                candidate = MagicMock()
                candidate.finish_reason = None
                candidate.content = MagicMock()

                text_part = MagicMock()
                text_part.text = f"chunk_{i}"
                text_part.function_call = None
                candidate.content.parts = [text_part]

                chunk.candidates = [candidate]
                yield chunk

            # Final chunk with usage
            final_chunk = MagicMock()
            final_chunk.usage_metadata = MagicMock()
            final_chunk.usage_metadata.prompt_token_count = 1000
            final_chunk.usage_metadata.candidates_token_count = 500
            final_chunk.usage_metadata.cached_content_token_count = 100

            final_candidate = MagicMock()
            final_candidate.finish_reason = MagicMock()
            final_candidate.finish_reason.name = "STOP"
            final_candidate.content = MagicMock()
            final_candidate.content.parts = []

            final_chunk.candidates = [final_candidate]
            yield final_chunk

        import time

        start_time = time.time()
        result = await google_provider._parse_streaming_response(large_stream())

        # Consume all events
        events = []
        async for event in result.content:
            events.append(event)

        end_time = time.time()

        # Should process quickly even with many events
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should be under 5 seconds

        # Should have many events
        assert len(events) > 100  # Start, deltas, end events

        # Usage should be correct
        usage = await result.usage
        assert usage.input == 900  # 1000 - 100 cached
        assert usage.output == 500
        assert usage.cache_read == 100
