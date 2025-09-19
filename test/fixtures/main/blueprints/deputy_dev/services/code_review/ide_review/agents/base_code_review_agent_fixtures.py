"""
Fixtures for testing BaseCodeReviewAgent.

This module provides comprehensive fixtures for testing various scenarios
of the BaseCodeReviewAgent class including different input combinations,
mock data, and edge cases.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    LLMCallResponseTypes,
    NonStreamingParsedLLMCallResponse,
    UserAndSystemMessages,
)

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels, LLMUsage
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)


# Mock context service fixtures
@pytest.fixture
def mock_context_service() -> MagicMock:
    """Create a mock IDE review context service."""
    context_service = MagicMock(spec=IdeReviewContextService)
    context_service.get_pr_diff = AsyncMock(return_value="test diff content")
    context_service.review_id = 123
    return context_service


# Mock LLM handler fixtures
@pytest.fixture
def mock_llm_handler() -> MagicMock:
    """Create a mock LLM handler."""
    handler = MagicMock()
    handler.prompt_handler_map = MagicMock()
    handler.start_llm_query = AsyncMock()
    return handler


# Mock prompt handler fixtures
@pytest.fixture
def mock_prompt_handler() -> MagicMock:
    """Create a mock prompt handler."""
    handler = MagicMock()
    handler.get_prompt.return_value = UserAndSystemMessages(
        system_message="Test system message", user_message="Test user message"
    )
    return handler


# UserAndSystemMessages fixtures
@pytest.fixture
def sample_user_and_system_messages() -> UserAndSystemMessages:
    """Create sample user and system messages."""
    return UserAndSystemMessages(
        system_message="You are a helpful code review assistant.",
        user_message="Please review this code for security vulnerabilities.",
    )


@pytest.fixture
def large_user_and_system_messages() -> UserAndSystemMessages:
    """Create large user and system messages for token limit testing."""
    large_content = "x" * 100000  # 100k characters
    return UserAndSystemMessages(system_message=f"System: {large_content}", user_message=f"User: {large_content}")


@pytest.fixture
def empty_user_and_system_messages() -> UserAndSystemMessages:
    """Create empty user and system messages."""
    return UserAndSystemMessages(system_message="", user_message="")


# LLM response fixtures
@pytest.fixture
def sample_llm_response() -> NonStreamingParsedLLMCallResponse:
    """Create a sample LLM response."""
    return NonStreamingParsedLLMCallResponse(
        type=LLMCallResponseTypes.NON_STREAMING,
        parsed_content=["Test response content"],
        content=[],
        usage={"input": 100, "output": 50},
        prompt_vars={},
        prompt_id="test_prompt",
        model_used=LLModels.GPT_4O.value,
        query_id=123,
    )


@pytest.fixture
def sample_llm_response_dual_pass() -> List[NonStreamingParsedLLMCallResponse]:
    """Create sample LLM responses for dual pass testing."""
    return [
        NonStreamingParsedLLMCallResponse(
            type=LLMCallResponseTypes.NON_STREAMING,
            parsed_content=["First pass response"],
            content=[],
            usage={"input": 100, "output": 50},
            prompt_vars={},
            prompt_id="test_prompt_1",
            model_used=LLModels.GPT_4O.value,
            query_id=123,
        ),
        NonStreamingParsedLLMCallResponse(
            type=LLMCallResponseTypes.NON_STREAMING,
            parsed_content=["Second pass response"],
            content=[],
            usage={"input": 120, "output": 60},
            prompt_vars={},
            prompt_id="test_prompt_2",
            model_used=LLModels.GPT_4O.value,
            query_id=124,
        ),
    ]


@pytest.fixture
def sample_llm_response_multiple_content() -> NonStreamingParsedLLMCallResponse:
    """Create a sample LLM response with multiple content blocks."""
    return NonStreamingParsedLLMCallResponse(
        type=LLMCallResponseTypes.NON_STREAMING,
        parsed_content=["Content block 1", "Content block 2", "Content block 3"],
        content=[],
        usage={"input": 150, "output": 75},
        prompt_vars={},
        prompt_id="test_prompt",
        model_used=LLModels.GPT_4O.value,
        query_id=125,
    )


# Agent run result fixtures
@pytest.fixture
def sample_agent_run_result_success() -> AgentRunResult:
    """Create a successful agent run result."""
    return AgentRunResult(
        agent_result="Successful agent execution",
        prompt_tokens_exceeded=False,
        agent_name="security",
        agent_type=AgentTypes.SECURITY,
        model=LLModels.GPT_4O.value,
        tokens_data={
            "securityPASS_1": {"system_prompt": 100, "user_prompt": 50, "input_tokens": 150, "output_tokens": 75}
        },
        display_name="Security Agent",
    )


@pytest.fixture
def sample_agent_run_result_token_exceeded() -> AgentRunResult:
    """Create an agent run result with token limit exceeded."""
    return AgentRunResult(
        agent_result=None,
        prompt_tokens_exceeded=True,
        agent_name="security",
        agent_type=AgentTypes.SECURITY,
        model=LLModels.GPT_4O,
        tokens_data={"securityPASS_1": {"system_prompt": 50000, "user_prompt": 50000}},
    )


@pytest.fixture
def sample_agent_run_result_dual_pass() -> AgentRunResult:
    """Create a dual pass agent run result."""
    return AgentRunResult(
        agent_result="Second pass final result",
        prompt_tokens_exceeded=False,
        agent_name="security",
        agent_type=AgentTypes.SECURITY,
        model=LLModels.GPT_4O,
        tokens_data={
            "securityPASS_1": {"system_prompt": 100, "user_prompt": 50, "input_tokens": 150, "output_tokens": 75},
            "securityPASS_2": {"system_prompt": 120, "user_prompt": 60, "input_tokens": 180, "output_tokens": 90},
        },
        display_name="Security Agent",
    )


# Configuration fixtures
@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create mock configuration for testing."""
    return {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}, "GPT_40_MINI": {"INPUT_TOKENS_LIMIT": 64000}}}


@pytest.fixture
def mock_config_low_token_limit() -> Dict[str, Any]:
    """Create mock configuration with low token limits for testing."""
    return {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 100}, "GPT_40_MINI": {"INPUT_TOKENS_LIMIT": 50}}}


# Edge case fixtures
@pytest.fixture
def invalid_llm_response() -> MagicMock:
    """Create an invalid LLM response (not NonStreamingParsedLLMCallResponse)."""
    return MagicMock(spec_set=["some_other_field"])


@pytest.fixture
def empty_prompt_variables() -> Dict[str, Optional[str]]:
    """Create empty prompt variables."""
    return {}


@pytest.fixture
def sample_prompt_variables() -> Dict[str, Optional[str]]:
    """Create sample prompt variables."""
    return {"code_content": "def test(): pass", "file_path": "/path/to/file.py", "context": "Testing context"}


@pytest.fixture
def prompt_variables_with_none_values() -> Dict[str, Optional[str]]:
    """Create prompt variables with None values."""
    return {"code_content": "def test(): pass", "file_path": None, "context": None}


# Test agent type scenarios
@pytest.fixture
def all_agent_types() -> List[AgentTypes]:
    """Get all available agent types for comprehensive testing."""
    return list(AgentTypes)


@pytest.fixture
def all_prompt_features() -> List[PromptFeatures]:
    """Get all available prompt features for comprehensive testing."""
    return list(PromptFeatures)


@pytest.fixture
def all_llm_models() -> List[LLModels]:
    """Get all available LLM models for comprehensive testing."""
    return list(LLModels)


# Error scenarios fixtures
@pytest.fixture
def llm_handler_with_exception() -> MagicMock:
    """Create an LLM handler that raises exceptions."""
    handler = MagicMock()
    handler.prompt_handler_map = MagicMock()
    handler.start_llm_query = AsyncMock(side_effect=Exception("LLM query failed"))
    return handler


@pytest.fixture
def context_service_with_exception() -> MagicMock:
    """Create a context service that raises exceptions."""
    service = MagicMock(spec=IdeReviewContextService)
    service.get_pr_diff = AsyncMock(side_effect=Exception("Context service failed"))
    service.review_id = 123
    return service


# Performance testing fixtures
@pytest.fixture
def large_tokens_data() -> Dict[str, Dict[str, Any]]:
    """Create large tokens data for performance testing."""
    return {
        f"agent_pass_{i}": {
            "system_prompt": 1000 + i,
            "user_prompt": 500 + i,
            "input_tokens": 1500 + i,
            "output_tokens": 750 + i,
        }
        for i in range(100)
    }


# Session ID fixtures
@pytest.fixture
def valid_session_id() -> int:
    """Valid session ID for testing."""
    return 12345


@pytest.fixture
def invalid_session_id() -> int:
    """Invalid session ID for testing."""
    return -1


@pytest.fixture
def zero_session_id() -> int:
    """Zero session ID for edge case testing."""
    return 0
