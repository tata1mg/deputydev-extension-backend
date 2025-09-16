"""
Fixtures for remaining Anthropic methods testing.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend_common.services.llm.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationTurn,
    UnifiedImageConversationTurnContent,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)


# User conversation turn fixtures
@pytest.fixture
def sample_user_conversation_turn() -> UserConversationTurn:
    """Sample user conversation turn with text content."""
    return UserConversationTurn(content=[UnifiedTextConversationTurnContent(text="Hello, how can you help me?")])


@pytest.fixture
def user_conversation_turn_with_image() -> UserConversationTurn:
    """User conversation turn with text and image content."""
    return UserConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="What do you see in this image?"),
            UnifiedImageConversationTurnContent(image_mimetype="image/jpeg", bytes_data=b"fake_image_data_here"),
        ]
    )


@pytest.fixture
def user_conversation_turn_with_cache_breakpoint() -> UserConversationTurn:
    """User conversation turn with cache breakpoint."""
    return UserConversationTurn(
        content=[UnifiedTextConversationTurnContent(text="This should be cached")], cache_breakpoint=True
    )


# Assistant conversation turn fixtures
@pytest.fixture
def sample_assistant_conversation_turn() -> AssistantConversationTurn:
    """Sample assistant conversation turn with text content."""
    return AssistantConversationTurn(
        content=[UnifiedTextConversationTurnContent(text="I can help you with various tasks!")]
    )


@pytest.fixture
def assistant_conversation_turn_with_tool_request() -> AssistantConversationTurn:
    """Assistant conversation turn with tool request."""
    return AssistantConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="Let me search for that information."),
            UnifiedToolRequestConversationTurnContent(
                tool_name="search_web", tool_use_id="tool_123", tool_input={"query": "python programming"}
            ),
        ]
    )


# Tool conversation turn fixtures
@pytest.fixture
def sample_tool_conversation_turn() -> ToolConversationTurn:
    """Sample tool conversation turn with response."""
    return ToolConversationTurn(
        content=[
            UnifiedToolResponseConversationTurnContent(
                tool_use_id="tool_123",
                tool_name="search_web",
                tool_use_response={"results": "Python is a programming language"},
            )
        ]
    )


@pytest.fixture
def multiple_tool_responses_turn() -> ToolConversationTurn:
    """Tool conversation turn with multiple responses."""
    return ToolConversationTurn(
        content=[
            UnifiedToolResponseConversationTurnContent(
                tool_use_id="tool_1", tool_name="search_tool", tool_use_response={"result": "First result"}
            ),
            UnifiedToolResponseConversationTurnContent(
                tool_use_id="tool_2", tool_name="process_tool", tool_use_response={"result": "Second result"}
            ),
        ]
    )


# Unified conversation turns list fixtures
@pytest.fixture
def mixed_unified_conversation_turns(
    sample_user_conversation_turn: UserConversationTurn,
    sample_assistant_conversation_turn: AssistantConversationTurn,
    sample_tool_conversation_turn: ToolConversationTurn,
) -> List[UnifiedConversationTurn]:
    """List with mixed conversation turn types."""
    return [sample_user_conversation_turn, sample_assistant_conversation_turn, sample_tool_conversation_turn]


@pytest.fixture
def complex_unified_conversation_turns(
    user_conversation_turn_with_image: UserConversationTurn,
    assistant_conversation_turn_with_tool_request: AssistantConversationTurn,
    multiple_tool_responses_turn: ToolConversationTurn,
) -> List[UnifiedConversationTurn]:
    """Complex conversation with multiple content types."""
    return [
        user_conversation_turn_with_image,
        assistant_conversation_turn_with_tool_request,
        multiple_tool_responses_turn,
    ]


# Region and model config fixtures
@pytest.fixture
def sample_model_config() -> Dict[str, Any]:
    """Sample model configuration for testing."""
    return {
        "PROVIDER_CONFIG": {
            "REGION_AND_IDENTIFIER_LIST": [
                {"AWS_REGION": "us-east-1", "MODEL_IDENTIFIER": "anthropic.claude-3-sonnet-20240229-v1:0"},
                {"AWS_REGION": "us-west-2", "MODEL_IDENTIFIER": "anthropic.claude-3-sonnet-20240229-v1:0"},
                {"AWS_REGION": "eu-west-1", "MODEL_IDENTIFIER": "anthropic.claude-3-sonnet-20240229-v1:0"},
            ]
        }
    }


# Non-streaming response fixtures
@pytest.fixture
def sample_invoke_model_response() -> Dict[str, Any]:
    """Sample InvokeModel response for non-streaming."""
    body_content = {
        "content": [{"type": "text", "text": "Hello! How can I help you today?"}],
        "usage": {
            "input_tokens": 15,
            "output_tokens": 8,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
    }

    # Create a mock body object that behaves like the real one
    mock_body = MagicMock()
    mock_body.read = AsyncMock(return_value=json.dumps(body_content).encode("utf-8"))

    return {"body": mock_body, "ResponseMetadata": {"RequestId": "test-request-123"}}


@pytest.fixture
def tool_use_invoke_model_response() -> Dict[str, Any]:
    """InvokeModel response with tool use."""
    body_content = {
        "content": [
            {"type": "text", "text": "I'll help you search for that information."},
            {"type": "tool_use", "id": "toolu_123", "name": "search_web", "input": {"query": "python programming"}},
        ],
        "usage": {
            "input_tokens": 25,
            "output_tokens": 45,
            "cache_read_input_tokens": 10,
            "cache_creation_input_tokens": 5,
        },
    }

    mock_body = MagicMock()
    mock_body.read = AsyncMock(return_value=json.dumps(body_content).encode("utf-8"))

    return {"body": mock_body, "ResponseMetadata": {"RequestId": "test-request-456"}}


# Token counting fixtures
@pytest.fixture
def sample_llm_payload_for_token_counting() -> Dict[str, Any]:
    """Sample LLM payload for token counting tests."""
    return {
        "system": "You are a helpful assistant.",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "Hello, how are you?"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "I'm doing well, thank you!"}]},
        ],
        "tools": [
            {
                "name": "search_web",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                },
            }
        ],
    }


@pytest.fixture
def complex_llm_payload_for_token_counting() -> Dict[str, Any]:
    """Complex LLM payload with various content types."""
    return {
        "system": [
            {
                "type": "text",
                "text": "You are a helpful assistant with access to tools.",
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please help me with this task"},
                    {"type": "tool_result", "tool_use_id": "tool_123", "content": {"result": "Some tool output"}},
                ],
            }
        ],
        "tools": [
            {
                "name": "file_processor",
                "description": "Process files",
                "input_schema": {
                    "type": "object",
                    "properties": {"file_path": {"type": "string"}, "action": {"type": "string"}},
                },
            }
        ],
    }


@pytest.fixture
def malformed_llm_payload_for_token_counting() -> Dict[str, Any]:
    """Malformed payload to test error handling."""
    return {
        "system": 123,  # Invalid type
        "messages": "invalid",  # Should be list
        "tools": None,
    }


# Mock service clients
@pytest.fixture
def mock_bedrock_service_client() -> MagicMock:
    """Mock BedrockServiceClient for testing."""
    mock_client = MagicMock()
    mock_client.get_llm_non_stream_response = AsyncMock()
    mock_client.get_llm_stream_response = AsyncMock()
    return mock_client


@pytest.fixture
def mock_tiktoken_client() -> MagicMock:
    """Mock TikToken client for token counting tests."""
    mock_client = MagicMock()
    mock_client.count = MagicMock(return_value=42)
    return mock_client


# Streaming response fixtures
@pytest.fixture
def mock_streaming_response() -> MagicMock:
    """Mock streaming response for testing."""
    mock_response = MagicMock()

    # Sample streaming events
    streaming_events = [
        {
            "chunk": {
                "bytes": json.dumps(
                    {"type": "content_block_start", "index": 0, "content_block": {"type": "text"}}
                ).encode("utf-8")
            }
        },
        {
            "chunk": {
                "bytes": json.dumps(
                    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}
                ).encode("utf-8")
            }
        },
        {"chunk": {"bytes": json.dumps({"type": "content_block_stop", "index": 0}).encode("utf-8")}},
        {
            "chunk": {
                "bytes": json.dumps(
                    {
                        "type": "message_stop",
                        "amazon-bedrock-invocationMetrics": {"inputTokenCount": 10, "outputTokenCount": 5},
                    }
                ).encode("utf-8")
            }
        },
    ]

    async def async_iter():
        for event in streaming_events:
            yield event

    mock_response["body"] = async_iter()
    return mock_response


@pytest.fixture
def mock_async_bedrock_client() -> MagicMock:
    """Mock async bedrock client for streaming tests."""
    mock_client = MagicMock()
    mock_client.__aexit__ = AsyncMock()
    return mock_client
