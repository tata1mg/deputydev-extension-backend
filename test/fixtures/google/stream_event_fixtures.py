"""
Stream event fixtures for Google/Gemini tests.

This module contains fixtures for testing Google streaming response parsing,
including various streaming scenarios and event types.
"""

from typing import Any
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_google_stream_text_chunk() -> MagicMock:
    """Mock Google stream chunk with text content."""
    chunk = MagicMock()
    chunk.usage_metadata = None
    
    candidate = MagicMock()
    candidate.finish_reason = None
    candidate.content = MagicMock()
    
    text_part = MagicMock()
    text_part.text = "Hello"
    text_part.function_call = None
    candidate.content.parts = [text_part]
    
    chunk.candidates = [candidate]
    return chunk


@pytest.fixture
def mock_google_stream_function_chunk() -> MagicMock:
    """Mock Google stream chunk with function call."""
    chunk = MagicMock()
    chunk.usage_metadata = None
    
    candidate = MagicMock()
    candidate.finish_reason = None
    candidate.content = MagicMock()
    
    function_part = MagicMock()
    function_part.text = None
    function_part.function_call = MagicMock()
    function_part.function_call.name = "get_weather"
    function_part.function_call.id = "call_123"
    function_part.function_call.args = {"location": "New York"}
    candidate.content.parts = [function_part]
    
    chunk.candidates = [candidate]
    return chunk


@pytest.fixture
def mock_google_stream_final_chunk() -> MagicMock:
    """Mock Google stream final chunk with usage information."""
    chunk = MagicMock()
    chunk.usage_metadata = MagicMock()
    chunk.usage_metadata.prompt_token_count = 100
    chunk.usage_metadata.candidates_token_count = 50
    chunk.usage_metadata.cached_content_token_count = 20
    
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    candidate.content = MagicMock()
    candidate.content.parts = []
    
    chunk.candidates = [candidate]
    return chunk


@pytest.fixture
def mock_google_stream_malformed_chunk() -> MagicMock:
    """Mock Google stream chunk with malformed function call."""
    chunk = MagicMock()
    chunk.usage_metadata = MagicMock()
    chunk.usage_metadata.prompt_token_count = 80
    chunk.usage_metadata.candidates_token_count = 25
    chunk.usage_metadata.cached_content_token_count = 10
    
    candidate = MagicMock()
    candidate.finish_reason = "MALFORMED_FUNCTION_CALL"
    candidate.finish_message = "Invalid function call format detected"
    candidate.content = MagicMock()
    candidate.content.parts = []
    
    chunk.candidates = [candidate]
    return chunk


@pytest.fixture
def mock_google_stream_multiple_parts_chunk() -> MagicMock:
    """Mock Google stream chunk with multiple content parts."""
    chunk = MagicMock()
    chunk.usage_metadata = None
    
    candidate = MagicMock()
    candidate.finish_reason = None
    candidate.content = MagicMock()
    
    # First part - text
    text_part = MagicMock()
    text_part.text = "I'll help you with that. "
    text_part.function_call = None
    
    # Second part - function call
    function_part = MagicMock()
    function_part.text = None
    function_part.function_call = MagicMock()
    function_part.function_call.name = "search_web"
    function_part.function_call.id = "call_456"
    function_part.function_call.args = {"query": "Python tutorials"}
    
    candidate.content.parts = [text_part, function_part]
    chunk.candidates = [candidate]
    return chunk


@pytest.fixture
def mock_google_complete_stream() -> Any:
    """Mock complete Google streaming response."""
    async def mock_stream():
        # Chunk 1: Text start
        chunk1 = MagicMock()
        chunk1.usage_metadata = None
        
        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()
        
        text_part1 = MagicMock()
        text_part1.text = "Let me help you"
        text_part1.function_call = None
        candidate1.content.parts = [text_part1]
        
        chunk1.candidates = [candidate1]
        yield chunk1
        
        # Chunk 2: Text continuation
        chunk2 = MagicMock()
        chunk2.usage_metadata = None
        
        candidate2 = MagicMock()
        candidate2.finish_reason = None
        candidate2.content = MagicMock()
        
        text_part2 = MagicMock()
        text_part2.text = " with that request."
        text_part2.function_call = None
        candidate2.content.parts = [text_part2]
        
        chunk2.candidates = [candidate2]
        yield chunk2
        
        # Chunk 3: Function call
        chunk3 = MagicMock()
        chunk3.usage_metadata = None
        
        candidate3 = MagicMock()
        candidate3.finish_reason = None
        candidate3.content = MagicMock()
        
        function_part = MagicMock()
        function_part.text = None
        function_part.function_call = MagicMock()
        function_part.function_call.name = "execute_task"
        function_part.function_call.id = "call_789"
        function_part.function_call.args = {"task": "process_data"}
        candidate3.content.parts = [function_part]
        
        chunk3.candidates = [candidate3]
        yield chunk3
        
        # Chunk 4: Final with usage
        chunk4 = MagicMock()
        chunk4.usage_metadata = MagicMock()
        chunk4.usage_metadata.prompt_token_count = 120
        chunk4.usage_metadata.candidates_token_count = 80
        chunk4.usage_metadata.cached_content_token_count = 30
        
        candidate4 = MagicMock()
        candidate4.finish_reason = MagicMock()
        candidate4.finish_reason.name = "STOP"
        candidate4.content = MagicMock()
        candidate4.content.parts = []
        
        chunk4.candidates = [candidate4]
        yield chunk4
    
    return mock_stream()


@pytest.fixture
def mock_google_stream_with_error() -> Any:
    """Mock Google streaming response that encounters an error."""
    async def mock_stream():
        # Chunk 1: Normal text
        chunk1 = MagicMock()
        chunk1.usage_metadata = None
        
        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()
        
        text_part = MagicMock()
        text_part.text = "Starting response..."
        text_part.function_call = None
        candidate1.content.parts = [text_part]
        
        chunk1.candidates = [candidate1]
        yield chunk1
        
        # Raise an error during streaming
        raise Exception("Streaming error occurred")
    
    return mock_stream()


@pytest.fixture
def mock_google_stream_max_tokens() -> Any:
    """Mock Google streaming response that hits max tokens."""
    async def mock_stream():
        # Chunk 1: Text content
        chunk1 = MagicMock()
        chunk1.usage_metadata = None
        
        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()
        
        text_part = MagicMock()
        text_part.text = "This is a very long response that will exceed"
        text_part.function_call = None
        candidate1.content.parts = [text_part]
        
        chunk1.candidates = [candidate1]
        yield chunk1
        
        # Final chunk with MAX_TOKENS finish reason
        chunk2 = MagicMock()
        chunk2.usage_metadata = MagicMock()
        chunk2.usage_metadata.prompt_token_count = 100
        chunk2.usage_metadata.candidates_token_count = 4096  # Hit max tokens
        chunk2.usage_metadata.cached_content_token_count = 20
        
        candidate2 = MagicMock()
        candidate2.finish_reason = MagicMock()
        candidate2.finish_reason.name = "MAX_TOKENS"
        candidate2.content = MagicMock()
        candidate2.content.parts = []
        
        chunk2.candidates = [candidate2]
        yield chunk2
    
    return mock_stream()


@pytest.fixture
def mock_google_stream_safety_block() -> Any:
    """Mock Google streaming response that gets blocked by safety filters."""
    async def mock_stream():
        # Chunk 1: Partial content before block
        chunk1 = MagicMock()
        chunk1.usage_metadata = None
        
        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()
        
        text_part = MagicMock()
        text_part.text = "I was about to provide information but"
        text_part.function_call = None
        candidate1.content.parts = [text_part]
        
        chunk1.candidates = [candidate1]
        yield chunk1
        
        # Final chunk with SAFETY block
        chunk2 = MagicMock()
        chunk2.usage_metadata = MagicMock()
        chunk2.usage_metadata.prompt_token_count = 50
        chunk2.usage_metadata.candidates_token_count = 15
        chunk2.usage_metadata.cached_content_token_count = 10
        
        candidate2 = MagicMock()
        candidate2.finish_reason = MagicMock()
        candidate2.finish_reason.name = "SAFETY"
        
        # Mock safety rating
        safety_rating = MagicMock()
        safety_rating.blocked = True
        safety_rating.category = MagicMock()
        safety_rating.category.name = "HARM_CATEGORY_DANGEROUS_CONTENT"
        candidate2.safety_ratings = [safety_rating]
        
        candidate2.content = MagicMock()
        candidate2.content.parts = []
        
        chunk2.candidates = [candidate2]
        yield chunk2
    
    return mock_stream()


@pytest.fixture
def mock_google_stream_function_with_complex_args() -> Any:
    """Mock Google stream with function call having complex arguments."""
    async def mock_stream():
        # Chunk 1: Function call with complex arguments
        chunk1 = MagicMock()
        chunk1.usage_metadata = None
        
        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()
        
        function_part = MagicMock()
        function_part.text = None
        function_part.function_call = MagicMock()
        function_part.function_call.name = "complex_function"
        function_part.function_call.id = "call_complex_123"
        function_part.function_call.args = {
            "nested": {
                "data": {
                    "values": [1, 2, 3],
                    "metadata": {"type": "array", "size": 3}
                }
            },
            "options": ["option1", "option2"],
            "config": {"enabled": True, "threshold": 0.85}
        }
        candidate1.content.parts = [function_part]
        
        chunk1.candidates = [candidate1]
        yield chunk1
        
        # Final chunk
        chunk2 = MagicMock()
        chunk2.usage_metadata = MagicMock()
        chunk2.usage_metadata.prompt_token_count = 150
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
def mock_google_stream_empty_chunks() -> Any:
    """Mock Google streaming response with empty chunks."""
    async def mock_stream():
        # Chunk 1: Empty content
        chunk1 = MagicMock()
        chunk1.usage_metadata = None
        
        candidate1 = MagicMock()
        candidate1.finish_reason = None
        candidate1.content = MagicMock()
        candidate1.content.parts = []  # Empty parts
        
        chunk1.candidates = [candidate1]
        yield chunk1
        
        # Chunk 2: Final with usage but no content
        chunk2 = MagicMock()
        chunk2.usage_metadata = MagicMock()
        chunk2.usage_metadata.prompt_token_count = 20
        chunk2.usage_metadata.candidates_token_count = 0
        chunk2.usage_metadata.cached_content_token_count = 5
        
        candidate2 = MagicMock()
        candidate2.finish_reason = MagicMock()
        candidate2.finish_reason.name = "STOP"
        candidate2.content = MagicMock()
        candidate2.content.parts = []
        
        chunk2.candidates = [candidate2]
        yield chunk2
    
    return mock_stream()