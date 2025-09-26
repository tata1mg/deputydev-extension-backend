"""
Shared fixtures for Google LLM provider tests.
"""

import pytest


@pytest.fixture
def google_provider():
    """Create a Google provider instance for testing."""
    from deputydev_core.llm_handler.providers.google.llm_provider import Google
    from deputydev_core.utils.config_manager import ConfigManager

    from app.backend_common.adapters.config_manager_adapter import ConfigManagerAdapter

    config_manager = ConfigManager()
    config_adapter = ConfigManagerAdapter(config_manager)
    gemini_config = config_adapter.get_gemini_config()
    return Google(gemini_config)
