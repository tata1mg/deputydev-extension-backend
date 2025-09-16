"""
Fixtures for OpenAI function/tool call stream events.

This module provides mock OpenAI function call events for testing
tool use request streaming functionality.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_function_call_added_event() -> MagicMock:
    """Mock response.output_item.added event for function calls."""
    event = MagicMock()
    event.type = "response.output_item.added"
    event.item = MagicMock()
    event.item.type = "function_call"
    event.item.name = "test_function"
    event.item.call_id = "call_123456"
    return event


@pytest.fixture
def mock_function_arguments_delta_event() -> MagicMock:
    """Mock response.function_call_arguments.delta event."""
    event = MagicMock()
    event.type = "response.function_call_arguments.delta"
    event.delta = '{"param": "value'
    return event


@pytest.fixture
def mock_function_arguments_done_event() -> MagicMock:
    """Mock response.function_call_arguments.done event."""
    event = MagicMock()
    event.type = "response.function_call_arguments.done"
    return event


def create_function_call_added_event(tool_name: str, call_id: str) -> MagicMock:
    """Factory function to create function call added events with custom parameters."""
    event = MagicMock()
    event.type = "response.output_item.added"
    event.item = MagicMock()
    event.item.type = "function_call"
    event.item.name = tool_name
    event.item.call_id = call_id
    return event


def create_function_arguments_delta_event(delta_text: str) -> MagicMock:
    """Factory function to create function arguments delta events with custom content."""
    event = MagicMock()
    event.type = "response.function_call_arguments.delta"
    event.delta = delta_text
    return event