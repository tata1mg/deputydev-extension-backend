"""
Fixtures for testing remaining Google/Gemini LLM Provider methods.

This module contains fixtures for testing methods like:
- call_service_client
- get_tokens 
- _extract_payload_content_for_token_counting
- Streaming response parsing
- Token counting methods

The fixtures follow .deputydevrules guidelines and provide comprehensive test data.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    LLMCallResponseTypes,
    NonStreamingResponse,
    StreamingResponse,
)


@pytest.fixture
def mock_google_llm_payload() -> Dict[str, Any]:
    """Mock LLM payload for Google service client calls."""
    # Mock Google types
    mock_part = MagicMock()
    mock_part.text = "You are a helpful assistant."
    
    mock_content = MagicMock()
    mock_content.role = "user"
    mock_content.parts = [MagicMock()]
    mock_content.parts[0].text = "What is the weather like today?"
    
    mock_tool = MagicMock()
    mock_tool.function_declarations = [MagicMock()]
    mock_tool.function_declarations[0].name = "get_weather"
    mock_tool.function_declarations[0].description = "Get weather information"
    
    return {
        "max_tokens": 4096,
        "contents": [mock_content],
        "tools": [mock_tool],
        "tool_config": None,
        "system_instruction": mock_part,
        "safety_settings": {}
    }


@pytest.fixture
def mock_google_llm_payload_with_tools() -> Dict[str, Any]:
    """Mock LLM payload with multiple tools."""
    # Mock Google types
    mock_system_part = MagicMock()
    mock_system_part.text = "You are a helpful assistant with access to tools."
    
    mock_content1 = MagicMock()
    mock_content1.role = "user"
    mock_content1.parts = [MagicMock()]
    mock_content1.parts[0].text = "Check the weather and search for news."
    
    mock_content2 = MagicMock()
    mock_content2.role = "model"
    mock_content2.parts = [MagicMock()]
    mock_content2.parts[0].text = "I'll help you with that."
    
    # Mock tools
    mock_weather_tool = MagicMock()
    mock_weather_tool.function_declarations = [MagicMock()]
    mock_weather_tool.function_declarations[0].name = "get_weather"
    mock_weather_tool.function_declarations[0].description = "Get weather information"
    
    mock_search_tool = MagicMock()
    mock_search_tool.function_declarations = [MagicMock()]
    mock_search_tool.function_declarations[0].name = "search_news"
    mock_search_tool.function_declarations[0].description = "Search for news articles"
    
    return {
        "max_tokens": 4096,
        "contents": [mock_content1, mock_content2],
        "tools": [mock_weather_tool, mock_search_tool],
        "tool_config": None,
        "system_instruction": mock_system_part,
        "safety_settings": {}
    }


@pytest.fixture
def mock_google_llm_payload_complex() -> Dict[str, Any]:
    """Mock complex LLM payload for comprehensive testing."""
    # Mock Google types with complex structure
    mock_system_part = MagicMock()
    mock_system_part.text = "You are a helpful coding assistant with access to development tools."
    
    # Multiple conversation turns
    mock_contents = []
    
    # User message
    user_content = MagicMock()
    user_content.role = "user"
    user_content.parts = [MagicMock()]
    user_content.parts[0].text = "How do I implement a binary search algorithm?"
    user_content.parts[0].function_response = None
    mock_contents.append(user_content)
    
    # Assistant response with function call
    assistant_content = MagicMock()
    assistant_content.role = "model"
    assistant_parts = [MagicMock(), MagicMock()]
    assistant_parts[0].text = "I'll help you implement a binary search algorithm."
    assistant_parts[0].function_response = None
    assistant_parts[1].text = None
    assistant_parts[1].function_call = MagicMock()
    assistant_parts[1].function_call.name = "code_executor"
    assistant_parts[1].function_call.args = {"language": "python", "code": "def binary_search(arr, target):"}
    assistant_parts[1].function_response = None
    assistant_content.parts = assistant_parts
    mock_contents.append(assistant_content)
    
    # Function response
    function_response_content = MagicMock()
    function_response_content.role = "user"
    function_response_content.parts = [MagicMock()]
    function_response_content.parts[0].text = None
    function_response_content.parts[0].function_response = "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1"
    mock_contents.append(function_response_content)
    
    # Mock tools
    mock_tools = []
    code_tool = MagicMock()
    code_tool.function_declarations = [MagicMock()]
    code_tool.function_declarations[0].name = "code_executor"
    code_tool.function_declarations[0].description = "Execute code and return results"
    mock_tools.append(code_tool)
    
    file_tool = MagicMock()
    file_tool.function_declarations = [MagicMock()]
    file_tool.function_declarations[0].name = "read_file"
    file_tool.function_declarations[0].description = "Read file contents"
    mock_tools.append(file_tool)
    
    return {
        "max_tokens": 8192,
        "contents": mock_contents,
        "tools": mock_tools,
        "tool_config": None,
        "system_instruction": mock_system_part,
        "safety_settings": {}
    }


@pytest.fixture
def empty_google_llm_payload() -> Dict[str, Any]:
    """Mock empty LLM payload."""
    return {
        "max_tokens": 4096,
        "contents": [],
        "tools": [],
        "tool_config": None,
        "system_instruction": None,
        "safety_settings": {}
    }


@pytest.fixture
def malformed_google_llm_payload() -> Dict[str, Any]:
    """Mock malformed LLM payload for error testing."""
    # Create non-serializable objects
    class NonSerializable:
        def __repr__(self) -> str:
            return "NonSerializable"
    
    mock_part = MagicMock()
    mock_part.text = "System message"
    
    mock_content = MagicMock()
    mock_content.role = "user"
    mock_content.parts = [MagicMock()]
    mock_content.parts[0].text = "Test message"
    
    # Tool with non-serializable content
    mock_tool = MagicMock()
    mock_tool.function_declarations = [MagicMock()]
    mock_tool.function_declarations[0].non_serializable = NonSerializable()
    
    return {
        "max_tokens": 4096,
        "contents": [mock_content],
        "tools": [mock_tool],
        "tool_config": None,
        "system_instruction": mock_part,
        "safety_settings": {}
    }


@pytest.fixture
def sample_content_for_token_counting() -> str:
    """Sample content string for token counting tests."""
    return """
    This is a sample text for token counting. It contains multiple sentences,
    some technical terms like 'algorithm', 'implementation', and 'optimization'.
    It also has punctuation marks, numbers like 123, and special characters!
    
    The purpose is to test how the Google token counting works with various
    content types and structures.
    """


@pytest.fixture
def mock_google_streaming_response() -> Any:
    """Mock streaming response for service client testing."""
    async def mock_stream():
        # Stream chunk with text
        chunk = MagicMock()
        chunk.usage_metadata = MagicMock()
        chunk.usage_metadata.prompt_token_count = 80
        chunk.usage_metadata.candidates_token_count = 50
        chunk.usage_metadata.cached_content_token_count = 20
        
        candidate = MagicMock()
        candidate.finish_reason = MagicMock()
        candidate.finish_reason.name = "STOP"
        candidate.content = MagicMock()
        
        text_part = MagicMock()
        text_part.text = "Streaming response content"
        text_part.function_call = None
        candidate.content.parts = [text_part]
        
        chunk.candidates = [candidate]
        yield chunk
    
    return mock_stream()


@pytest.fixture
def mock_google_service_client() -> MagicMock:
    """Mock GeminiServiceClient for testing."""
    client = MagicMock()
    
    # Mock non-streaming response
    mock_non_stream_response = MagicMock()
    mock_non_stream_response.usage_metadata = MagicMock()
    mock_non_stream_response.usage_metadata.prompt_token_count = 100
    mock_non_stream_response.usage_metadata.candidates_token_count = 75
    mock_non_stream_response.usage_metadata.cached_content_token_count = 25
    
    candidate = MagicMock()
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    candidate.safety_ratings = []
    candidate.content = MagicMock()
    
    text_part = MagicMock()
    text_part.text = "Test response from service client"
    text_part.function_call = None
    candidate.content.parts = [text_part]
    
    mock_non_stream_response.candidates = [candidate]
    mock_non_stream_response.prompt_feedback = None
    
    client.get_llm_non_stream_response = AsyncMock(return_value=mock_non_stream_response)
    
    # Mock streaming response
    async def mock_stream():
        chunk = MagicMock()
        chunk.usage_metadata = MagicMock()
        chunk.usage_metadata.prompt_token_count = 80
        chunk.usage_metadata.candidates_token_count = 50
        chunk.usage_metadata.cached_content_token_count = 20
        
        candidate = MagicMock()
        candidate.finish_reason = MagicMock()
        candidate.finish_reason.name = "STOP"
        candidate.content = MagicMock()
        
        text_part = MagicMock()
        text_part.text = "Streaming test response"
        text_part.function_call = None
        candidate.content.parts = [text_part]
        
        chunk.candidates = [candidate]
        yield chunk
    
    client.get_llm_stream_response = AsyncMock(return_value=mock_stream())
    
    # Mock token counting
    client.get_tokens = AsyncMock(return_value=42)
    
    return client


@pytest.fixture
def mock_model_config() -> Dict[str, Any]:
    """Mock model configuration for Google models."""
    return {
        "NAME": "gemini-2.5-pro",
        "MAX_TOKENS": 8192,
        "THINKING_BUDGET_TOKENS": 4096,
        "TEMPERATURE": 0.7
    }


@pytest.fixture
def google_payload_with_list_content() -> Dict[str, Any]:
    """Mock Google payload with list-type content for token counting testing."""
    mock_system_part = MagicMock()
    mock_system_part.text = "Test system message"
    
    # Mock content with multiple parts of different types
    mock_content = MagicMock()
    mock_content.role = "user"
    mock_content.parts = []
    
    # Text part 1
    text_part1 = MagicMock()
    text_part1.text = "First text part"
    text_part1.function_call = None
    text_part1.function_response = None
    mock_content.parts.append(text_part1)
    
    # Text part 2
    text_part2 = MagicMock()
    text_part2.text = "Second text part"
    text_part2.function_call = None
    text_part2.function_response = None
    mock_content.parts.append(text_part2)
    
    # Function response part
    function_part = MagicMock()
    function_part.text = None
    function_part.function_call = None
    function_part.function_response = "test_function response"  # Use string instead of dict for easier string conversion
    mock_content.parts.append(function_part)
    
    # Image/bytes part (should be ignored in token counting)
    image_part = MagicMock()
    image_part.text = None
    image_part.function_call = None
    image_part.function_response = None
    image_part.inline_data = MagicMock()
    image_part.inline_data.mime_type = "image/png"
    mock_content.parts.append(image_part)
    
    return {
        "max_tokens": 4096,
        "contents": [mock_content],
        "tools": [],
        "tool_config": None,
        "system_instruction": mock_system_part,
        "safety_settings": {}
    }