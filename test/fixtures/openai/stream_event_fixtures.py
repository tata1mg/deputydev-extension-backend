"""
Fixtures for OpenAI stream event testing.

This module provides mock OpenAI stream events for testing the
OpenAI LLM provider's stream parsing functionality.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_response_completed_event() -> MagicMock:
    """Mock response.completed event with usage data."""
    event = MagicMock()
    event.type = "response.completed"
    event.response = MagicMock()
    event.response.usage = MagicMock()
    event.response.usage.input_tokens = 100
    event.response.usage.output_tokens = 50
    event.response.usage.input_tokens_details = MagicMock()
    event.response.usage.input_tokens_details.cached_tokens = 20
    return event


@pytest.fixture
def mock_response_completed_without_usage() -> MagicMock:
    """Mock response.completed event without usage information."""
    event = MagicMock()
    event.type = "response.completed"
    event.response = MagicMock()
    event.response.usage = None
    return event


@pytest.fixture
def mock_response_completed_incomplete_usage() -> MagicMock:
    """Mock response.completed event with incomplete usage data."""
    event = MagicMock()
    event.type = "response.completed"
    event.response = MagicMock()
    event.response.usage = MagicMock()
    # Missing some usage fields
    event.response.usage.input_tokens = 50
    event.response.usage.output_tokens = None
    event.response.usage.input_tokens_details = None
    return event