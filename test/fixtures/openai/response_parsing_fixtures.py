"""
Fixtures for testing OpenAI response parsing methods.

This module contains fixtures for testing OpenAI response parsing functionality,
including non-streaming response parsing, service client calls, and various
response structures.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
import pytest

from openai.types.responses import Response
from openai.types.responses.response_stream_event import ResponseStreamEvent
from app.backend_common.models.dto.message_thread_dto import LLModels, LLMUsage
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
)


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Mock OpenAI Response object with message output."""
    response = MagicMock(spec=Response)
    
    # Mock output with message type
    message_output = MagicMock()
    message_output.type = "message"
    
    response.output = [message_output]
    response.output_text = "Hello, I can help you with that!"
    
    # Mock usage
    usage = MagicMock()
    usage.input_tokens = 100
    usage.output_tokens = 50
    usage_details = MagicMock()
    usage_details.cached_tokens = 20
    usage.input_tokens_details = usage_details
    
    response.usage = usage
    
    return response


@pytest.fixture
def mock_openai_response_with_function_call() -> MagicMock:
    """Mock OpenAI Response object with function call output."""
    response = MagicMock(spec=Response)
    
    # Mock output with function call type
    function_output = MagicMock()
    function_output.type = "function_call"
    function_output.arguments = '{"query": "test query", "limit": 10}'
    function_output.name = "search_function"
    function_output.call_id = "call_12345"
    
    response.output = [function_output]
    
    # Mock usage
    usage = MagicMock()
    usage.input_tokens = 150
    usage.output_tokens = 75
    usage_details = MagicMock()
    usage_details.cached_tokens = 30
    usage.input_tokens_details = usage_details
    
    response.usage = usage
    
    return response


@pytest.fixture
def mock_openai_response_new_format() -> MagicMock:
    """Mock OpenAI Response object with new format structure."""
    response = MagicMock(spec=Response)
    
    # Mock output with message type and content array
    message_output = MagicMock()
    message_output.type = "message"
    
    content_piece = MagicMock()
    content_piece.type = "output_text"
    content_piece.text = "This is the response text"
    
    message_output.content = [content_piece]
    
    response.output = [message_output]
    
    # Mock usage
    usage = MagicMock()
    usage.input_tokens = 120
    usage.output_tokens = 60
    usage_details = MagicMock()
    usage_details.cached_tokens = 25
    usage.input_tokens_details = usage_details
    
    response.usage = usage
    
    return response


@pytest.fixture
def mock_openai_response_new_format_with_function() -> MagicMock:
    """Mock OpenAI Response object with new format function call."""
    response = MagicMock(spec=Response)
    
    # Mock output with function call type and parsed arguments
    function_output = MagicMock()
    function_output.type = "function_call"
    function_output.name = "get_weather"
    function_output.call_id = "call_weather_123"
    
    # Mock parsed_arguments as a pydantic-like object
    parsed_args = MagicMock()
    parsed_args.model_dump.return_value = {"location": "New York", "units": "celsius"}
    function_output.parsed_arguments = parsed_args
    
    response.output = [function_output]
    
    # Mock usage
    usage = MagicMock()
    usage.input_tokens = 200
    usage.output_tokens = 100
    usage_details = MagicMock()
    usage_details.cached_tokens = 40
    usage.input_tokens_details = usage_details
    
    response.usage = usage
    
    return response


@pytest.fixture
def mock_openai_response_without_usage() -> MagicMock:
    """Mock OpenAI Response object without usage information."""
    response = MagicMock(spec=Response)
    
    message_output = MagicMock()
    message_output.type = "message"
    
    response.output = [message_output]
    response.output_text = "Response without usage"
    response.usage = None
    
    return response


@pytest.fixture
def mock_streaming_response() -> AsyncMock:
    """Mock streaming response from OpenAI."""
    async def mock_stream():
        # Mock text block start
        event1 = MagicMock(spec=ResponseStreamEvent)
        event1.type = "response.output_item.added"
        event1.item = MagicMock()
        event1.item.type = "message"
        yield event1
        
        # Mock text delta
        event2 = MagicMock(spec=ResponseStreamEvent)
        event2.type = "response.output_text.delta"
        event2.delta = "Hello"
        yield event2
        
        # Mock text delta
        event3 = MagicMock(spec=ResponseStreamEvent)
        event3.type = "response.output_text.delta"
        event3.delta = " world!"
        yield event3
        
        # Mock text done
        event4 = MagicMock(spec=ResponseStreamEvent)
        event4.type = "response.output_text.done"
        yield event4
        
        # Mock response completed with usage
        event5 = MagicMock(spec=ResponseStreamEvent)
        event5.type = "response.completed"
        event5.response = MagicMock()
        event5.response.usage = MagicMock()
        event5.response.usage.input_tokens = 100
        event5.response.usage.output_tokens = 50
        event5.response.usage.input_tokens_details = MagicMock()
        event5.response.usage.input_tokens_details.cached_tokens = 20
        yield event5
    
    return mock_stream()


@pytest.fixture
def mock_llm_payload() -> Dict[str, Any]:
    """Mock LLM payload for service client calls."""
    return {
        "conversation_messages": [
            {"role": "user", "content": [{"type": "input_text", "text": "Hello"}]}
        ],
        "system_message": "You are a helpful assistant",
        "tools": [],
        "tool_choice": "auto",
        "max_tokens": 4096
    }


@pytest.fixture
def mock_llm_payload_with_tools() -> Dict[str, Any]:
    """Mock LLM payload with tools for service client calls."""
    return {
        "conversation_messages": [
            {"role": "user", "content": [{"type": "input_text", "text": "What's the weather?"}]}
        ],
        "system_message": "You are a weather assistant",
        "tools": [
            {
                "name": "get_weather",
                "description": "Get weather information",
                "type": "function",
                "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
            }
        ],
        "tool_choice": "auto",
        "max_tokens": 4096
    }


@pytest.fixture
def mock_llm_payload_complex() -> Dict[str, Any]:
    """Mock complex LLM payload for token counting tests."""
    return {
        "system_message": "You are a helpful coding assistant with deep knowledge of Python.",
        "conversation_messages": [
            {
                "role": "user", 
                "content": [
                    {"type": "input_text", "text": "How do I implement a binary search?"}
                ]
            },
            {
                "role": "assistant",
                "content": "Here's a Python implementation of binary search:"
            },
            {
                "type": "function_call_output",
                "call_id": "call_123",
                "output": json.dumps({"code": "def binary_search(arr, target): ..."})
            }
        ],
        "tools": [
            {
                "name": "code_executor",
                "description": "Execute Python code",
                "parameters": {"type": "object", "properties": {"code": {"type": "string"}}}
            }
        ]
    }


@pytest.fixture 
def sample_content_for_token_counting() -> str:
    """Sample text content for token counting tests."""
    return """
    This is a sample text for testing token counting functionality.
    It includes multiple sentences, some code examples like:
    
    def hello_world():
        print("Hello, World!")
        return "success"
    
    And some JSON data: {"key": "value", "number": 42}
    """


@pytest.fixture
def empty_llm_payload() -> Dict[str, Any]:
    """Empty LLM payload for edge case testing."""
    return {
        "system_message": "",
        "conversation_messages": [],
        "tools": []
    }


@pytest.fixture
def malformed_llm_payload() -> Dict[str, Any]:
    """Malformed LLM payload for error handling tests."""
    return {
        "conversation_messages": [
            {"role": "user", "content": None},  # Malformed content
            {"invalid_structure": "test"}
        ],
        "tools": "not_a_list",  # Should be a list
        "system_message": None
    }