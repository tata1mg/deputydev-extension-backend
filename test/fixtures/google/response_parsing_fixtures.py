"""
Response parsing fixtures for Google/Gemini tests.

This module contains fixtures for testing Google response parsing methods,
including various response types and scenarios.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_google_response() -> MagicMock:
    """Mock Google GenerateContentResponse with text content only."""
    response = MagicMock()

    # Mock usage metadata
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 100
    response.usage_metadata.candidates_token_count = 50
    response.usage_metadata.cached_content_token_count = 20

    # Mock candidate
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    candidate.safety_ratings = []

    # Mock content with text part
    candidate.content = MagicMock()
    text_part = MagicMock()
    text_part.text = "Hello, I can help you with that!"
    text_part.function_call = None
    candidate.content.parts = [text_part]

    response.candidates = [candidate]
    response.prompt_feedback = None

    return response


@pytest.fixture
def mock_google_response_with_function_call() -> MagicMock:
    """Mock Google response with function call."""
    response = MagicMock()

    # Mock usage metadata
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 150
    response.usage_metadata.candidates_token_count = 75
    response.usage_metadata.cached_content_token_count = 30

    # Mock candidate
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    candidate.safety_ratings = []

    # Mock content with function call part
    candidate.content = MagicMock()
    function_part = MagicMock()
    function_part.text = None
    function_part.function_call = MagicMock()
    function_part.function_call.name = "search_function"
    function_part.function_call.args = {"query": "test query", "limit": 10}
    candidate.content.parts = [function_part]

    response.candidates = [candidate]
    response.prompt_feedback = None

    return response


@pytest.fixture
def mock_google_response_without_usage() -> MagicMock:
    """Mock Google response without usage information."""
    response = MagicMock()
    response.usage_metadata = None

    # Mock candidate
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    candidate.safety_ratings = []

    # Mock content with text part
    candidate.content = MagicMock()
    text_part = MagicMock()
    text_part.text = "Response without usage data"
    text_part.function_call = None
    candidate.content.parts = [text_part]

    response.candidates = [candidate]
    response.prompt_feedback = None

    return response


@pytest.fixture
def mock_google_response_blocked() -> MagicMock:
    """Mock Google response that was blocked by safety filters."""
    response = MagicMock()

    # Mock usage metadata
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 50
    response.usage_metadata.candidates_token_count = 0
    response.usage_metadata.cached_content_token_count = 10

    # Mock candidate with safety block
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "SAFETY"

    # Mock safety rating that blocked the response
    safety_rating = MagicMock()
    safety_rating.blocked = True
    safety_rating.category = MagicMock()
    safety_rating.category.name = "HARM_CATEGORY_HARASSMENT"
    candidate.safety_ratings = [safety_rating]

    candidate.content = None
    response.candidates = [candidate]
    response.prompt_feedback = MagicMock()

    return response


@pytest.fixture
def mock_google_response_no_candidates() -> MagicMock:
    """Mock Google response with no candidates."""
    response = MagicMock()

    # Mock usage metadata
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 25
    response.usage_metadata.candidates_token_count = 0
    response.usage_metadata.cached_content_token_count = 5

    response.candidates = []
    response.prompt_feedback = MagicMock()
    response.prompt_feedback.block_reason = "BLOCKED_REASON_UNSPECIFIED"

    return response


@pytest.fixture
def mock_google_response_max_tokens() -> MagicMock:
    """Mock Google response that hit max tokens limit."""
    response = MagicMock()

    # Mock usage metadata
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 120
    response.usage_metadata.candidates_token_count = 1000
    response.usage_metadata.cached_content_token_count = 0

    # Mock candidate
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "MAX_TOKENS"
    candidate.safety_ratings = []

    # Mock partial content
    candidate.content = MagicMock()
    text_part = MagicMock()
    text_part.text = "This is a partial response that was cut off due to"
    text_part.function_call = None
    candidate.content.parts = [text_part]

    response.candidates = [candidate]
    response.prompt_feedback = None

    return response


@pytest.fixture
def mock_google_response_mixed_content() -> MagicMock:
    """Mock Google response with mixed content types."""
    response = MagicMock()

    # Mock usage metadata
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 200
    response.usage_metadata.candidates_token_count = 100
    response.usage_metadata.cached_content_token_count = 40

    # Mock candidate
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    candidate.safety_ratings = []

    # Mock content with both text and function call
    candidate.content = MagicMock()

    text_part = MagicMock()
    text_part.text = "I'll help you with that task."
    text_part.function_call = None

    function_part = MagicMock()
    function_part.text = None
    function_part.function_call = MagicMock()
    function_part.function_call.name = "execute_task"
    function_part.function_call.args = {"action": "process", "data": {"key": "value"}}

    candidate.content.parts = [text_part, function_part]

    response.candidates = [candidate]
    response.prompt_feedback = None

    return response


@pytest.fixture
def mock_google_streaming_response() -> Any:
    """Mock Google streaming response for testing."""

    async def mock_stream():
        # Stream chunk 1 - text start
        chunk1 = MagicMock()
        chunk1.usage_metadata = None

        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()

        text_part1 = MagicMock()
        text_part1.text = "Hello"
        text_part1.function_call = None
        candidate1.content.parts = [text_part1]

        chunk1.candidates = [candidate1]
        yield chunk1

        # Stream chunk 2 - text continuation
        chunk2 = MagicMock()
        chunk2.usage_metadata = None

        candidate2 = MagicMock()
        candidate2.finish_reason = None
        candidate2.content = MagicMock()

        text_part2 = MagicMock()
        text_part2.text = " there!"
        text_part2.function_call = None
        candidate2.content.parts = [text_part2]

        chunk2.candidates = [candidate2]
        yield chunk2

        # Stream chunk 3 - final with usage
        chunk3 = MagicMock()
        chunk3.usage_metadata = MagicMock()
        chunk3.usage_metadata.prompt_token_count = 100
        chunk3.usage_metadata.candidates_token_count = 50
        chunk3.usage_metadata.cached_content_token_count = 20

        candidate3 = MagicMock()
        candidate3.finish_reason = MagicMock()
        candidate3.finish_reason.name = "STOP"
        candidate3.content = MagicMock()
        candidate3.content.parts = []

        chunk3.candidates = [candidate3]
        yield chunk3

    return mock_stream()


@pytest.fixture
def mock_google_streaming_with_function_call() -> Any:
    """Mock Google streaming response with function call."""

    async def mock_stream():
        # Stream chunk 1 - function call
        chunk1 = MagicMock()
        chunk1.usage_metadata = None

        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()

        function_part = MagicMock()
        function_part.text = None
        function_part.function_call = MagicMock()
        function_part.function_call.name = "get_weather"
        function_part.function_call.id = "call_weather_123"
        function_part.function_call.args = {"location": "New York"}
        candidate1.content.parts = [function_part]

        chunk1.candidates = [candidate1]
        yield chunk1

        # Stream chunk 2 - final with usage
        chunk2 = MagicMock()
        chunk2.usage_metadata = MagicMock()
        chunk2.usage_metadata.prompt_token_count = 160
        chunk2.usage_metadata.candidates_token_count = 100
        chunk2.usage_metadata.cached_content_token_count = 40

        candidate2 = MagicMock()
        candidate2.finish_reason = MagicMock()
        candidate2.finish_reason.name = "STOP"
        candidate2.content = MagicMock()
        candidate2.content.parts = []

        chunk2.candidates = [candidate2]
        yield chunk2

    return mock_stream()


@pytest.fixture
def mock_google_streaming_malformed() -> Any:
    """Mock Google streaming response with malformed function call."""

    async def mock_stream():
        # Stream chunk 1 - malformed function call
        chunk1 = MagicMock()
        chunk1.usage_metadata = MagicMock()
        chunk1.usage_metadata.prompt_token_count = 80
        chunk1.usage_metadata.candidates_token_count = 25
        chunk1.usage_metadata.cached_content_token_count = 10

        candidate1 = MagicMock()
        candidate1.finish_reason = "MALFORMED_FUNCTION_CALL"
        candidate1.finish_message = "Invalid function call format"
        candidate1.content = MagicMock()
        candidate1.content.parts = []

        chunk1.candidates = [candidate1]
        yield chunk1

    return mock_stream()
