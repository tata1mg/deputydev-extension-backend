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
    from deputydev_core.llm_handler.providers.google.llm_provider import Google

    # Mock config for testing
    mock_config = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "12345",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com",
        "location": "us-central1",
    }

    return Google(config=mock_config)
