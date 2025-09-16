"""
Fixtures for unknown and edge-case OpenAI stream events.

This module provides mock events for testing error handling
and unknown event types.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_unknown_event() -> MagicMock:
    """Mock unknown/unhandled event type."""
    event = MagicMock()
    event.type = "unknown.event.type"
    return event


@pytest.fixture
def mock_output_item_added_unknown_type() -> MagicMock:
    """Mock output_item.added with unknown item type."""
    event = MagicMock()
    event.type = "response.output_item.added"
    event.item = MagicMock()
    event.item.type = "unknown_item_type"
    return event


def create_usage_event(input_tokens: int, output_tokens: int, cached_tokens: int) -> MagicMock:
    """Factory function to create usage events with custom token values."""
    event = MagicMock()
    event.type = "response.completed"
    event.response = MagicMock()
    event.response.usage = MagicMock()
    event.response.usage.input_tokens = input_tokens
    event.response.usage.output_tokens = output_tokens
    event.response.usage.input_tokens_details = MagicMock()
    event.response.usage.input_tokens_details.cached_tokens = cached_tokens
    return event