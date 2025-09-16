"""
Fixtures for Anthropic stream event testing.

This module provides mock Anthropic stream events for testing the
Anthropic LLM provider's stream parsing functionality.
"""

from typing import Any, Dict

import pytest


@pytest.fixture
def mock_message_stop_event() -> Dict[str, Any]:
    """Mock message_stop event with usage data."""
    return {
        "type": "message_stop",
        "amazon-bedrock-invocationMetrics": {
            "inputTokenCount": 100,
            "outputTokenCount": 50,
            "cacheReadInputTokenCount": 20,
            "cacheWriteInputTokenCount": 10,
        },
    }


@pytest.fixture
def mock_message_stop_without_usage() -> Dict[str, Any]:
    """Mock message_stop event without usage information."""
    return {"type": "message_stop", "amazon-bedrock-invocationMetrics": {}}


@pytest.fixture
def mock_message_stop_incomplete_usage() -> Dict[str, Any]:
    """Mock message_stop event with incomplete usage data."""
    return {
        "type": "message_stop",
        "amazon-bedrock-invocationMetrics": {
            "inputTokenCount": 50,
            # Missing other usage fields
        },
    }


@pytest.fixture
def mock_thinking_block_start_event() -> Dict[str, Any]:
    """Mock content_block_start event for thinking blocks."""
    return {"type": "content_block_start", "content_block": {"type": "thinking"}}


@pytest.fixture
def mock_redacted_thinking_block_start_event() -> Dict[str, Any]:
    """Mock content_block_start event for redacted thinking blocks."""
    return {
        "type": "content_block_start",
        "content_block": {"type": "redacted_thinking", "data": "This thinking has been redacted"},
    }


@pytest.fixture
def mock_thinking_delta_event() -> Dict[str, Any]:
    """Mock content_block_delta event for thinking delta."""
    return {
        "type": "content_block_delta",
        "delta": {"type": "thinking_delta", "thinking": "I need to think about this problem..."},
    }


@pytest.fixture
def mock_signature_delta_event() -> Dict[str, Any]:
    """Mock content_block_delta event for signature delta."""
    return {"type": "content_block_delta", "delta": {"type": "signature_delta", "signature": "signature_123"}}


@pytest.fixture
def mock_tool_use_block_start_event() -> Dict[str, Any]:
    """Mock content_block_start event for tool use blocks."""
    return {
        "type": "content_block_start",
        "content_block": {"type": "tool_use", "name": "test_function", "id": "tool_use_123"},
    }


@pytest.fixture
def mock_input_json_delta_event() -> Dict[str, Any]:
    """Mock content_block_delta event for input JSON delta."""
    return {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": '{"param": "value"'}}


@pytest.fixture
def mock_tool_use_block_stop_event() -> Dict[str, Any]:
    """Mock content_block_stop event for tool use blocks."""
    return {"type": "content_block_stop"}


@pytest.fixture
def mock_text_block_start_event() -> Dict[str, Any]:
    """Mock content_block_start event for text blocks."""
    return {"type": "content_block_start", "content_block": {"type": "text"}}


@pytest.fixture
def mock_text_delta_event() -> Dict[str, Any]:
    """Mock content_block_delta event for text delta."""
    return {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello, world!"}}


@pytest.fixture
def mock_text_block_stop_event() -> Dict[str, Any]:
    """Mock content_block_stop event for text blocks."""
    return {"type": "content_block_stop"}


@pytest.fixture
def mock_unknown_event() -> Dict[str, Any]:
    """Mock unknown/unhandled event type."""
    return {"type": "unknown_event_type", "data": "some_data"}


def create_message_stop_event(
    input_tokens: int, output_tokens: int, cache_read_tokens: int = 0, cache_write_tokens: int = 0
) -> Dict[str, Any]:
    """Factory function to create message_stop events with custom token counts."""
    return {
        "type": "message_stop",
        "amazon-bedrock-invocationMetrics": {
            "inputTokenCount": input_tokens,
            "outputTokenCount": output_tokens,
            "cacheReadInputTokenCount": cache_read_tokens,
            "cacheWriteInputTokenCount": cache_write_tokens,
        },
    }


def create_tool_use_start_event(tool_name: str, tool_id: str) -> Dict[str, Any]:
    """Factory function to create tool use start events with custom parameters."""
    return {"type": "content_block_start", "content_block": {"type": "tool_use", "name": tool_name, "id": tool_id}}


def create_input_json_delta_event(json_delta: str) -> Dict[str, Any]:
    """Factory function to create input JSON delta events with custom content."""
    return {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": json_delta}}


def create_text_delta_event(text: str) -> Dict[str, Any]:
    """Factory function to create text delta events with custom content."""
    return {"type": "content_block_delta", "delta": {"type": "text_delta", "text": text}}


def create_thinking_delta_event(thinking_text: str) -> Dict[str, Any]:
    """Factory function to create thinking delta events with custom content."""
    return {"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": thinking_text}}
