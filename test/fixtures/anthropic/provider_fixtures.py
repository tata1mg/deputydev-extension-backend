"""
Provider-level fixtures for Anthropic tests.

This module provides fixtures that are commonly used across different
Anthropic provider test modules.
"""

import pytest


@pytest.fixture
def anthropic_provider():
    """Create a fresh Anthropic provider instance for each test."""
    # Import here to avoid module-level import issues
    from deputydev_core.llm_handler.providers.anthropic.llm_provider import Anthropic

    return Anthropic()
