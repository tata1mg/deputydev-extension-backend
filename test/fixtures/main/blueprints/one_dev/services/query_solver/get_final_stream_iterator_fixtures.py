"""
Fixtures for testing QuerySolver.get_final_stream_iterator method.

This module provides comprehensive fixtures for testing various scenarios
of the get_final_stream_iterator method including different streaming events,
mock responses, and edge cases.
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    ParsedLLMCallResponse,
    StreamingEventType,
    StreamingParsedLLMCallResponse,
    TextBlockDelta,
    TextBlockDeltaContent,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestDeltaContent,
    ToolUseRequestEnd,
    ToolUseRequestStart,
    ToolUseRequestStartContent,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    Reasoning,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockDeltaContent,
    CodeBlockEnd,
    CodeBlockEndContent,
    CodeBlockStart,
    CodeBlockStartContent,
    StreamingContentBlockType,
    ThinkingBlockDelta,
    ThinkingBlockDeltaContent,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)


@pytest.fixture
def mock_llm_handler_for_stream() -> MagicMock:
    """Create a mock LLM handler for stream iterator tests."""
    from unittest.mock import Mock

    from app.backend_common.services.llm.dataclasses.main import NonStreamingParsedLLMCallResponse
    from app.backend_common.services.llm.handler import LLMHandler

    handler = MagicMock(spec=LLMHandler)

    # Create a mock NonStreamingParsedLLMCallResponse for query summary generation
    mock_non_streaming_response = Mock(spec=NonStreamingParsedLLMCallResponse)
    mock_parsed_content = Mock()
    mock_parsed_content.summary = "Test summary"
    mock_parsed_content.success = True
    mock_non_streaming_response.parsed_content = [mock_parsed_content]

    handler.start_llm_query = AsyncMock(return_value=mock_non_streaming_response)
    return handler


@pytest.fixture
def basic_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a basic streaming response for testing."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 123

    # Create a simple awaitable mock for testing
    class AwaitableMock:
        def __init__(self):
            self.awaited = False
            self.await_count = 0

        def __await__(self):
            self.awaited = True
            self.await_count += 1
            return iter([None])

        def assert_awaited_once(self):
            assert self.awaited, "Mock was not awaited"
            assert self.await_count == 1, f"Expected to be awaited once, but was awaited {self.await_count} times"

    response.llm_response_storage_task = AwaitableMock()

    # Create mock content that yields text blocks
    async def mock_content():
        yield TextBlockStart(type=StreamingEventType.TEXT_BLOCK_START)
        yield TextBlockDelta(type=StreamingEventType.TEXT_BLOCK_DELTA, content=TextBlockDeltaContent(text="Hello "))
        yield TextBlockDelta(type=StreamingEventType.TEXT_BLOCK_DELTA, content=TextBlockDeltaContent(text="World!"))
        yield TextBlockEnd(type=StreamingEventType.TEXT_BLOCK_END)

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def tool_use_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with tool use events."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 456

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        yield ToolUseRequestStart(
            type=StreamingEventType.TOOL_USE_REQUEST_START,
            content=ToolUseRequestStartContent(tool_name="test_tool", tool_use_id="tool-use-123"),
        )
        yield ToolUseRequestDelta(
            type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
            content=ToolUseRequestDeltaContent(input_params_json_delta='{"param": "'),
        )
        yield ToolUseRequestDelta(
            type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
            content=ToolUseRequestDeltaContent(input_params_json_delta='value"}'),
        )
        yield ToolUseRequestEnd(type=StreamingEventType.TOOL_USE_REQUEST_END)

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def thinking_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with thinking blocks."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 789

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        yield ThinkingBlockStart(type=StreamingContentBlockType.THINKING_BLOCK_START, ignore_in_chat=False)
        yield ThinkingBlockDelta(
            type=StreamingContentBlockType.THINKING_BLOCK_DELTA,
            content=ThinkingBlockDeltaContent(thinking_delta="I need to "),
        )
        yield ThinkingBlockDelta(
            type=StreamingContentBlockType.THINKING_BLOCK_DELTA,
            content=ThinkingBlockDeltaContent(thinking_delta="think about this..."),
        )
        yield ThinkingBlockEnd(type=StreamingContentBlockType.THINKING_BLOCK_END)

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def code_block_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with code blocks."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 101

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        yield CodeBlockStart(
            type=StreamingContentBlockType.CODE_BLOCK_START,
            content=CodeBlockStartContent(language="python", filepath="/test/file.py", is_diff=False),
        )
        yield CodeBlockDelta(
            type=StreamingContentBlockType.CODE_BLOCK_DELTA, content=CodeBlockDeltaContent(code_delta="def test():\n")
        )
        yield CodeBlockDelta(
            type=StreamingContentBlockType.CODE_BLOCK_DELTA, content=CodeBlockDeltaContent(code_delta="    return True")
        )
        yield CodeBlockEnd(type=StreamingContentBlockType.CODE_BLOCK_END, content=CodeBlockEndContent(diff="true"))

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def mixed_content_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with mixed content types."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 202

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        # Text block
        yield TextBlockStart(type=StreamingEventType.TEXT_BLOCK_START)
        yield TextBlockDelta(
            type=StreamingEventType.TEXT_BLOCK_DELTA, content=TextBlockDeltaContent(text="Let me analyze this...")
        )
        yield TextBlockEnd(type=StreamingEventType.TEXT_BLOCK_END)

        # Thinking block
        yield ThinkingBlockStart(type=StreamingContentBlockType.THINKING_BLOCK_START, ignore_in_chat=False)
        yield ThinkingBlockDelta(
            type=StreamingContentBlockType.THINKING_BLOCK_DELTA,
            content=ThinkingBlockDeltaContent(thinking_delta="First, I'll..."),
        )
        yield ThinkingBlockEnd(type=StreamingContentBlockType.THINKING_BLOCK_END)

        # Code block
        yield CodeBlockStart(
            type=StreamingContentBlockType.CODE_BLOCK_START,
            content=CodeBlockStartContent(language="javascript", filepath="/src/test.js", is_diff=False),
        )
        yield CodeBlockDelta(
            type=StreamingContentBlockType.CODE_BLOCK_DELTA,
            content=CodeBlockDeltaContent(code_delta="function test() { return 'test'; }"),
        )
        yield CodeBlockEnd(type=StreamingContentBlockType.CODE_BLOCK_END, content=CodeBlockEndContent(diff=None))

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def empty_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create an empty streaming response."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 303

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        # No content yielded
        return
        yield  # This line won't be reached but satisfies the generator requirement

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def cancelled_task_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response that simulates task cancellation."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 404

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        yield TextBlockStart(type=StreamingEventType.TEXT_BLOCK_START)
        # Simulate cancellation after first event
        current_task = asyncio.current_task()
        if current_task:
            current_task.cancel()
        yield TextBlockDelta(
            type=StreamingEventType.TEXT_BLOCK_DELTA, content=MagicMock(text="This should not be processed")
        )

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def malformed_tool_use_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with malformed tool use."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 505

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        yield MagicMock(type=StreamingEventType.MALFORMED_TOOL_USE_REQUEST)

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def mock_generate_query_summary_success() -> tuple[str, bool]:
    """Mock successful query summary generation."""
    return ("Test query summary", True)


@pytest.fixture
def mock_generate_query_summary_failure() -> tuple[Optional[str], bool]:
    """Mock failed query summary generation."""
    return (None, False)


@pytest.fixture
def mock_generate_query_summary_timeout() -> AsyncMock:
    """Mock query summary generation that times out."""

    async def timeout_summary(*args, **kwargs):
        await asyncio.sleep(6)  # Longer than the 5-second timeout
        return ("Timeout summary", True)

    return AsyncMock(side_effect=timeout_summary)


@pytest.fixture
def stream_iterator_params() -> Dict[str, Any]:
    """Basic parameters for get_final_stream_iterator method."""
    return {
        "session_id": 123,
        "query_id": "123",
        "previous_queries": ["previous query 1", "previous query 2"],
        "llm_model": LLModels.GPT_4_POINT_1,
        "agent_name": "test_agent",
        "reasoning": None,
    }


@pytest.fixture
def stream_iterator_params_with_reasoning() -> Dict[str, Any]:
    """Parameters for get_final_stream_iterator method with reasoning."""
    return {
        "session_id": 456,
        "query_id": "456",
        "previous_queries": [],
        "llm_model": LLModels.CLAUDE_3_POINT_5_SONNET,
        "agent_name": "reasoning_agent",
        "reasoning": Reasoning.MEDIUM,
    }


@pytest.fixture
def large_previous_queries_list() -> List[str]:
    """Create a large list of previous queries for testing."""
    return [f"Query number {i}" for i in range(100)]


@pytest.fixture
def special_characters_params() -> Dict[str, Any]:
    """Parameters with special characters for edge case testing."""
    return {
        "session_id": 789,
        "query_id": "789",
        "previous_queries": ["Query with émojis 😊", "Query with 中文", "Query with symbols !@#$%^&*()"],
        "llm_model": LLModels.GEMINI_2_POINT_5_PRO,
        "agent_name": "special_agent_🤖",
        "reasoning": None,
    }


@pytest.fixture
def non_streaming_response() -> ParsedLLMCallResponse:
    """Create a non-streaming response to test error handling."""
    response = MagicMock()
    response.query_id = 999
    return response


@pytest.fixture
def mock_thinking_block_with_ignore_chat():
    """Create a thinking block that should be ignored in chat."""
    start_block = ThinkingBlockStart(type=StreamingContentBlockType.THINKING_BLOCK_START, ignore_in_chat=True)
    delta_block = ThinkingBlockDelta(
        type=StreamingContentBlockType.THINKING_BLOCK_DELTA,
        content=ThinkingBlockDeltaContent(thinking_delta="Internal reasoning..."),
        ignore_in_chat=True,
    )
    end_block = ThinkingBlockEnd(type=StreamingContentBlockType.THINKING_BLOCK_END)

    return start_block, delta_block, end_block


@pytest.fixture
def complex_tool_use_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with complex tool use scenario."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 606

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        # Multiple tool uses in sequence
        yield ToolUseRequestStart(
            type=StreamingEventType.TOOL_USE_REQUEST_START,
            content=ToolUseRequestStartContent(tool_name="file_reader", tool_use_id="tool-1"),
        )
        yield ToolUseRequestDelta(
            type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
            content=ToolUseRequestDeltaContent(input_params_json_delta='{"file_path": "/test/file.py"}'),
        )
        yield ToolUseRequestEnd(type=StreamingEventType.TOOL_USE_REQUEST_END)

        # Another tool use
        yield ToolUseRequestStart(
            type=StreamingEventType.TOOL_USE_REQUEST_START,
            content=ToolUseRequestStartContent(tool_name="grep_search", tool_use_id="tool-2"),
        )
        yield ToolUseRequestDelta(
            type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
            content=ToolUseRequestDeltaContent(input_params_json_delta='{"query": "test", "file": "*.py"}'),
        )
        yield ToolUseRequestEnd(type=StreamingEventType.TOOL_USE_REQUEST_END)

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def incomplete_blocks_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with incomplete blocks."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 707

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        # Start a text block but don't end it
        yield TextBlockStart(type=StreamingEventType.TEXT_BLOCK_START)
        yield TextBlockDelta(
            type=StreamingEventType.TEXT_BLOCK_DELTA, content=TextBlockDeltaContent(text="Incomplete text...")
        )
        # Missing TextBlockEnd

        # Start a code block but don't end it
        yield CodeBlockStart(
            type=StreamingContentBlockType.CODE_BLOCK_START,
            content=CodeBlockStartContent(language="python", filepath="/incomplete.py", is_diff=False),
        )
        yield CodeBlockDelta(
            type=StreamingContentBlockType.CODE_BLOCK_DELTA,
            content=CodeBlockDeltaContent(code_delta="def incomplete():"),
        )
        # Missing CodeBlockEnd

    response.parsed_content = mock_content()
    return response


@pytest.fixture
def json_parsing_error_tool_response() -> StreamingParsedLLMCallResponse:
    """Create a streaming response with invalid JSON in tool parameters."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = 808

    async def mock_storage_task():
        return None

    response.llm_response_storage_task = mock_storage_task()

    async def mock_content():
        yield ToolUseRequestStart(
            type=StreamingEventType.TOOL_USE_REQUEST_START,
            content=ToolUseRequestStartContent(tool_name="test_tool", tool_use_id="json-error-tool"),
        )
        yield ToolUseRequestDelta(
            type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
            content=ToolUseRequestDeltaContent(input_params_json_delta='{"invalid": json}'),  # Invalid JSON
        )
        yield ToolUseRequestEnd(type=StreamingEventType.TOOL_USE_REQUEST_END)

    response.parsed_content = mock_content()
    return response
