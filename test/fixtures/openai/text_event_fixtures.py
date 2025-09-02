"""
Fixtures for OpenAI text/message stream events.

This module provides mock OpenAI text and message events for testing
text block streaming functionality.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_message_added_event() -> MagicMock:
    """Mock response.output_item.added event for messages."""
    event = MagicMock()
    event.type = "response.output_item.added"
    event.item = MagicMock()
    event.item.type = "message"
    return event


@pytest.fixture
def mock_output_text_delta_event() -> MagicMock:
    """Mock response.output_text.delta event."""
    event = MagicMock()
    event.type = "response.output_text.delta"
    event.delta = "Hello, world!"
    return event


@pytest.fixture
def mock_output_text_done_event() -> MagicMock:
    """Mock response.output_text.done event."""
    event = MagicMock()
    event.type = "response.output_text.done"
    return event


def create_text_delta_event(delta_text: str) -> MagicMock:
    """Factory function to create text delta events with custom content."""
    event = MagicMock()
    event.type = "response.output_text.delta"
    event.delta = delta_text
    return event