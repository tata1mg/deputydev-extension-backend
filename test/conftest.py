"""
Global test configuration and fixtures for DeputyDev test suite.

This module provides shared fixtures and configuration that will be
automatically available to all tests in the project.

IMPORTANT: ConfigManager must be initialized at module import time because
many modules (like constants.py) use ConfigManager at import time.
"""

from unittest.mock import patch

import pytest

# Initialize ConfigManager immediately when conftest.py is imported
# This ensures it's available before any other module imports occur
from deputydev_core.utils.config_manager import ConfigManager

ConfigManager.initialize()


@pytest.fixture(scope="session", autouse=True)
def config_manager_session():
    """
    Provide access to the initialized ConfigManager for tests that need it.

    The actual initialization happens at module import time above,
    this fixture just provides access to the initialized instance.
    """
    return ConfigManager


@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """
    Mock external dependencies that are commonly used across tests.

    This fixture automatically mocks external services like TikToken, AppLogger,
    and database connections.
    """
    from unittest.mock import Mock

    from app.backend_common.services.llm.dataclasses.main import NonStreamingParsedLLMCallResponse

    # Create a mock NonStreamingParsedLLMCallResponse
    mock_non_streaming_response = Mock(spec=NonStreamingParsedLLMCallResponse)
    mock_non_streaming_response.parsed_content = [Mock(text="Test summary")]

    with (
        patch("deputydev_core.services.tiktoken.TikToken") as mock_tiktoken,
        patch("deputydev_core.utils.app_logger.AppLogger") as mock_app_logger,
        patch(
            "app.main.blueprints.one_dev.services.repository.agent_chats.repository.AgentChatsRepository.get_chats_by_session_id"
        ) as mock_get_chats,
        patch(
            "app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto.QuerySummarysRepository.get_query_summary"
        ) as mock_get_query_summary,
        patch(
            "app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto.QuerySummarysRepository.update_query_summary"
        ) as mock_update_query_summary,
        patch(
            "app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto.QuerySummarysRepository.create_query_summary"
        ) as mock_create_query_summary,
    ):
        # Configure the database mocks
        mock_get_chats.return_value = []
        mock_get_query_summary.return_value = None
        mock_update_query_summary.return_value = None
        mock_create_query_summary.return_value = None

        # Yield the mocks in case tests need to configure them
        yield {
            "tiktoken": mock_tiktoken,
            "app_logger": mock_app_logger,
            "get_chats_by_session_id": mock_get_chats,
            "mock_non_streaming_response": mock_non_streaming_response,
        }
