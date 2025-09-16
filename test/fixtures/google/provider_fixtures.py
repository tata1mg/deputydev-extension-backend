"""
Provider-level fixtures for Google/Gemini tests.

This module provides fixtures that are commonly used across different
Google provider test modules.
"""

import pytest


@pytest.fixture
def google_provider():
    """Create a fresh Google provider instance for each test."""
    # Import here to avoid module-level import issues
    from app.backend_common.services.llm.providers.google.llm_provider import Google

    return Google()
