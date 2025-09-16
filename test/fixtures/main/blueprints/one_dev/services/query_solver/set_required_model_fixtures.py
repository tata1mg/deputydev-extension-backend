"""
Fixtures for testing QuerySolver._set_required_model method.

This module provides comprehensive fixtures for testing various scenarios
of the _set_required_model method including different model changes,
session states, and retry reasons.
"""

from typing import Optional
from unittest.mock import MagicMock
from datetime import datetime

import pytest

from app.backend_common.models.dto.extension_sessions_dto import ExtensionSessionDTO
from app.backend_common.models.dto.message_thread_dto import LLModels
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    InfoMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    Reasoning,
    RetryReasons,
)


@pytest.fixture
def mock_existing_session_different_model() -> ExtensionSessionDTO:
    """Create mock existing session with different model."""
    return ExtensionSessionDTO(
        id=1,
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        current_model=LLModels.GPT_4_POINT_1_NANO,
        summary="Test session",
        status="ACTIVE",
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00"),
    )


@pytest.fixture
def mock_existing_session_same_model() -> ExtensionSessionDTO:
    """Create mock existing session with same model."""
    return ExtensionSessionDTO(
        id=1,
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        current_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        summary="Test session",
        status="ACTIVE",
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00"),
    )


@pytest.fixture
def mock_existing_session_premium_model() -> ExtensionSessionDTO:
    """Create mock existing session with premium model."""
    return ExtensionSessionDTO(
        id=1,
        session_id=456,
        user_team_id=2,
        session_type="premium_session",
        current_model=LLModels.CLAUDE_4_SONNET,
        summary="Premium session",
        status="ACTIVE",
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00"),
    )


@pytest.fixture
def mock_new_session_data() -> ExtensionSessionDTO:
    """Create mock new session data for creation."""
    return ExtensionSessionDTO(
        id=1,
        session_id=789,
        user_team_id=3,
        session_type="new_session_type",
        current_model=LLModels.GEMINI_2_POINT_5_PRO,
        summary=None,
        status="ACTIVE",
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00"),
    )


@pytest.fixture
def basic_set_model_params() -> dict:
    """Basic parameters for _set_required_model method."""
    return {
        "llm_model": LLModels.CLAUDE_3_POINT_5_SONNET,
        "session_id": 123,
        "query_id": "test-query-id",
        "agent_name": "test_agent",
        "retry_reason": None,
        "user_team_id": 1,
        "session_type": "test_session",
        "reasoning": None,
    }


@pytest.fixture
def model_change_params() -> dict:
    """Parameters for model change scenario."""
    return {
        "llm_model": LLModels.CLAUDE_4_SONNET,
        "session_id": 123,
        "query_id": "model-change-query-id",
        "agent_name": "advanced_agent",
        "retry_reason": None,
        "user_team_id": 1,
        "session_type": "test_session",
        "reasoning": Reasoning.HIGH,
    }


@pytest.fixture
def tool_use_failed_retry_params() -> dict:
    """Parameters for tool use failed retry scenario."""
    return {
        "llm_model": LLModels.GPT_4_POINT_1,
        "session_id": 456,
        "query_id": "retry-tool-failed-id",
        "agent_name": "fallback_agent",
        "retry_reason": RetryReasons.TOOL_USE_FAILED,
        "user_team_id": 2,
        "session_type": "premium_session",
        "reasoning": Reasoning.MEDIUM,
    }


@pytest.fixture
def throttled_retry_params() -> dict:
    """Parameters for throttled retry scenario."""
    return {
        "llm_model": LLModels.GEMINI_2_POINT_5_FLASH,
        "session_id": 456,
        "query_id": "retry-throttled-id",
        "agent_name": "fallback_agent",
        "retry_reason": RetryReasons.THROTTLED,
        "user_team_id": 2,
        "session_type": "premium_session",
        "reasoning": Reasoning.LOW,
    }


@pytest.fixture
def token_limit_exceeded_retry_params() -> dict:
    """Parameters for token limit exceeded retry scenario."""
    return {
        "llm_model": LLModels.GPT_4_POINT_1_MINI,
        "session_id": 456,
        "query_id": "retry-token-limit-id",
        "agent_name": "compact_agent",
        "retry_reason": RetryReasons.TOKEN_LIMIT_EXCEEDED,
        "user_team_id": 2,
        "session_type": "premium_session",
        "reasoning": Reasoning.MINIMAL,
    }


@pytest.fixture
def new_session_params() -> dict:
    """Parameters for new session creation scenario."""
    return {
        "llm_model": LLModels.GEMINI_2_POINT_5_PRO,
        "session_id": 789,
        "query_id": "new-session-query-id",
        "agent_name": "default_agent",
        "retry_reason": None,
        "user_team_id": 3,
        "session_type": "new_session_type",
        "reasoning": Reasoning.HIGH,
    }


@pytest.fixture
def advanced_model_change_params() -> dict:
    """Parameters for advanced model change scenario."""
    return {
        "llm_model": LLModels.OPENROUTER_GPT_5,
        "session_id": 999,
        "query_id": "advanced-model-id",
        "agent_name": "advanced_ai_agent",
        "retry_reason": None,
        "user_team_id": 4,
        "session_type": "enterprise_session",
        "reasoning": Reasoning.HIGH,
    }


@pytest.fixture
def expected_info_message_data_no_retry() -> InfoMessageData:
    """Expected info message data for model change without retry reason."""
    return InfoMessageData(
        info="LLM model changed from GPT_4_POINT_1_NANO to CLAUDE_3_POINT_5_SONNET by the user."
    )


@pytest.fixture
def expected_info_message_data_tool_failed() -> InfoMessageData:
    """Expected info message data for tool use failed retry."""
    return InfoMessageData(
        info="LLM model changed from CLAUDE_4_SONNET to GPT_4_POINT_1 due to tool use failure."
    )


@pytest.fixture
def expected_info_message_data_throttled() -> InfoMessageData:
    """Expected info message data for throttled retry."""
    return InfoMessageData(
        info="LLM model changed from CLAUDE_4_SONNET to GEMINI_2_POINT_5_FLASH due to throttling."
    )


@pytest.fixture
def expected_info_message_data_token_limit() -> InfoMessageData:
    """Expected info message data for token limit exceeded retry."""
    return InfoMessageData(
        info="LLM model changed from CLAUDE_4_SONNET to GPT_4_POINT_1_MINI due to token limit exceeded."
    )


@pytest.fixture
def expected_agent_chat_create_request_no_retry() -> AgentChatCreateRequest:
    """Expected agent chat create request for model change without retry."""
    return AgentChatCreateRequest(
        session_id=123,
        actor=ActorType.SYSTEM,
        message_data=InfoMessageData(
            info="LLM model changed from GPT_4_POINT_1_NANO to CLAUDE_3_POINT_5_SONNET by the user."
        ),
        message_type=ChatMessageType.INFO,
        metadata={
            "llm_model": LLModels.CLAUDE_3_POINT_5_SONNET.value,
            "agent_name": "test_agent",
        },
        query_id="test-query-id",
        previous_queries=[],
    )


@pytest.fixture
def expected_agent_chat_create_request_with_reasoning() -> AgentChatCreateRequest:
    """Expected agent chat create request with reasoning metadata."""
    return AgentChatCreateRequest(
        session_id=123,
        actor=ActorType.SYSTEM,
        message_data=InfoMessageData(
            info="LLM model changed from GPT_4_POINT_1_NANO to CLAUDE_4_SONNET by the user."
        ),
        message_type=ChatMessageType.INFO,
        metadata={
            "llm_model": LLModels.CLAUDE_4_SONNET.value,
            "agent_name": "advanced_agent",
            "reasoning": Reasoning.HIGH.value,
        },
        query_id="model-change-query-id",
        previous_queries=[],
    )


@pytest.fixture
def expected_agent_chat_create_request_tool_failed() -> AgentChatCreateRequest:
    """Expected agent chat create request for tool use failed retry."""
    return AgentChatCreateRequest(
        session_id=456,
        actor=ActorType.SYSTEM,
        message_data=InfoMessageData(
            info="LLM model changed from CLAUDE_4_SONNET to GPT_4_POINT_1 due to tool use failure."
        ),
        message_type=ChatMessageType.INFO,
        metadata={
            "llm_model": LLModels.GPT_4_POINT_1.value,
            "agent_name": "fallback_agent",
            "reasoning": Reasoning.MEDIUM.value,
        },
        query_id="retry-tool-failed-id",
        previous_queries=[],
    )


@pytest.fixture
def expected_agent_chat_create_request_throttled() -> AgentChatCreateRequest:
    """Expected agent chat create request for throttled retry."""
    return AgentChatCreateRequest(
        session_id=456,
        actor=ActorType.SYSTEM,
        message_data=InfoMessageData(
            info="LLM model changed from CLAUDE_4_SONNET to GEMINI_2_POINT_5_FLASH due to throttling."
        ),
        message_type=ChatMessageType.INFO,
        metadata={
            "llm_model": LLModels.GEMINI_2_POINT_5_FLASH.value,
            "agent_name": "fallback_agent",
            "reasoning": Reasoning.LOW.value,
        },
        query_id="retry-throttled-id",
        previous_queries=[],
    )


@pytest.fixture
def expected_agent_chat_create_request_token_limit() -> AgentChatCreateRequest:
    """Expected agent chat create request for token limit exceeded retry."""
    return AgentChatCreateRequest(
        session_id=456,
        actor=ActorType.SYSTEM,
        message_data=InfoMessageData(
            info="LLM model changed from CLAUDE_4_SONNET to GPT_4_POINT_1_MINI due to token limit exceeded."
        ),
        message_type=ChatMessageType.INFO,
        metadata={
            "llm_model": LLModels.GPT_4_POINT_1_MINI.value,
            "agent_name": "compact_agent",
            "reasoning": Reasoning.MINIMAL.value,
        },
        query_id="retry-token-limit-id",
        previous_queries=[],
    )


@pytest.fixture
def mock_config_manager_models() -> list:
    """Mock configuration for model display names."""
    return [
        {"name": "GPT_4_POINT_1_NANO", "display_name": "GPT-4.1 Nano"},
        {"name": "CLAUDE_3_POINT_5_SONNET", "display_name": "Claude 3.5 Sonnet"},
        {"name": "CLAUDE_4_SONNET", "display_name": "Claude 4 Sonnet"},
        {"name": "GPT_4_POINT_1", "display_name": "GPT-4.1"},
        {"name": "GEMINI_2_POINT_5_FLASH", "display_name": "Gemini 2.5 Flash"},
        {"name": "GPT_4_POINT_1_MINI", "display_name": "GPT-4.1 Mini"},
        {"name": "GEMINI_2_POINT_5_PRO", "display_name": "Gemini 2.5 Pro"},
        {"name": "OPENROUTER_GPT_5", "display_name": "GPT-5 (OpenRouter)"},
    ]


@pytest.fixture
def model_upgrade_scenario_params() -> dict:
    """Parameters for model upgrade scenario (free to premium)."""
    return {
        "llm_model": LLModels.CLAUDE_4_SONNET,
        "session_id": 111,
        "query_id": "upgrade-scenario-id",
        "agent_name": "premium_agent",
        "retry_reason": None,
        "user_team_id": 5,
        "session_type": "upgraded_session",
        "reasoning": Reasoning.HIGH,
    }


@pytest.fixture
def model_downgrade_scenario_params() -> dict:
    """Parameters for model downgrade scenario (premium to free)."""
    return {
        "llm_model": LLModels.GPT_4_POINT_1_NANO,
        "session_id": 222,
        "query_id": "downgrade-scenario-id",
        "agent_name": "basic_agent",
        "retry_reason": None,
        "user_team_id": 6,
        "session_type": "basic_session",
        "reasoning": Reasoning.LOW,
    }


@pytest.fixture
def edge_case_long_names_params() -> dict:
    """Parameters for edge case with long model and agent names."""
    return {
        "llm_model": LLModels.OPENROUTER_GPT_5,
        "session_id": 333,
        "query_id": "very-long-query-id-with-multiple-hyphens-and-descriptive-text",
        "agent_name": "very_long_descriptive_agent_name_with_underscores_and_detailed_description",
        "retry_reason": RetryReasons.TOKEN_LIMIT_EXCEEDED,
        "user_team_id": 7,
        "session_type": "edge_case_session_type_with_long_descriptive_name",
        "reasoning": Reasoning.HIGH,
    }


@pytest.fixture
def multiple_retry_reasons_params() -> list:
    """List of parameters for testing all retry reasons."""
    base_params = {
        "llm_model": LLModels.GEMINI_2_POINT_5_PRO,
        "session_id": 444,
        "query_id": "multi-retry-test-id",
        "agent_name": "retry_test_agent",
        "user_team_id": 8,
        "session_type": "retry_test_session",
        "reasoning": Reasoning.MEDIUM,
    }
    
    return [
        {**base_params, "retry_reason": RetryReasons.TOOL_USE_FAILED},
        {**base_params, "retry_reason": RetryReasons.THROTTLED},
        {**base_params, "retry_reason": RetryReasons.TOKEN_LIMIT_EXCEEDED},
        {**base_params, "retry_reason": None},
    ]


@pytest.fixture
def mock_empty_config_models() -> list:
    """Mock empty configuration for testing fallback behavior."""
    return []


@pytest.fixture
def mock_partial_config_models() -> list:
    """Mock partial configuration with missing display names."""
    return [
        {"name": "GPT_4_POINT_1_NANO"},  # Missing display_name
        {"name": "CLAUDE_3_POINT_5_SONNET", "display_name": "Claude 3.5 Sonnet"},
        {"name": "UNKNOWN_MODEL", "display_name": "Unknown Model"},
    ]