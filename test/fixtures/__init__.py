"""
Test fixtures package for DeputyDev.

This package contains organized test fixtures for different components
and services in the application.

Structure:
- openai/: OpenAI LLM provider-specific fixtures
"""

# Import commonly used fixtures for easy access
from .openai import openai_provider

__all__ = [
    "openai_provider",
]
