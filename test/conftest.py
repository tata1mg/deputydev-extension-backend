"""
Global test configuration and fixtures for DeputyDev test suite.

This module provides shared fixtures and configuration that will be 
automatically available to all tests in the project.

IMPORTANT: ConfigManager must be initialized at module import time because
many modules (like constants.py) use ConfigManager at import time.
"""

import pytest
from unittest.mock import patch

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
    
    This fixture automatically mocks external services like TikToken and AppLogger
    that are not part of the code being tested but are dependencies.
    """
    with patch('deputydev_core.services.tiktoken.TikToken') as mock_tiktoken, \
         patch('deputydev_core.utils.app_logger.AppLogger') as mock_app_logger:
        
        # Yield the mocks in case tests need to configure them
        yield {
            'tiktoken': mock_tiktoken,
            'app_logger': mock_app_logger
        }