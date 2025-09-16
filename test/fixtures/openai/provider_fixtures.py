"""
Provider-level fixtures for OpenAI tests.

This module provides fixtures that are commonly used across different
OpenAI provider test modules.
"""

import pytest


@pytest.fixture
def openai_provider():
    """Create a fresh OpenAI provider instance for each test."""
    # Import here to avoid module-level import issues
    from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI

    return OpenAI()
