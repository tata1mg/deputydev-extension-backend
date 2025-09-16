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
    from app.backend_common.services.llm.providers.anthropic.llm_provider import Anthropic

    return Anthropic()
