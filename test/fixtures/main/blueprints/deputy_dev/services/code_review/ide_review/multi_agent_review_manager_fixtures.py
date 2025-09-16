"""
Fixtures for MultiAgentWebSocketManager tests.

This module provides fixtures for testing the MultiAgentWebSocketManager class,
including sample data, mocked objects, and test configurations.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    RequestType,
    WebSocketMessage,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager import (
    MultiAgentWebSocketManager,
)


@pytest.fixture
def sample_multi_agent_manager() -> MultiAgentWebSocketManager:
    """Create a sample MultiAgentWebSocketManager for testing."""
    return MultiAgentWebSocketManager(connection_id="test-connection-123", review_id=456, is_local=True)


@pytest.fixture
def sample_agent_request_query() -> AgentRequestItem:
    """Create a sample agent request with query type."""
    return AgentRequestItem(
        agent_id=101,
        review_id=456,
        type=RequestType.QUERY,
        payload={"content": "Please review this code for security issues", "session_id": 789},
    )


@pytest.fixture
def sample_agent_request_tool_use_response() -> AgentRequestItem:
    """Create a sample agent request with tool use response type."""
    return AgentRequestItem(
        agent_id=102,
        review_id=456,
        type=RequestType.TOOL_USE_RESPONSE,
        payload={"tool_response": "File contents: def hello(): pass", "session_id": 789},
    )


@pytest.fixture
def sample_agent_request_list_single(sample_agent_request_query: AgentRequestItem) -> List[AgentRequestItem]:
    """Create a single agent request list."""
    return [sample_agent_request_query]


@pytest.fixture
def sample_agent_request_list_multiple() -> List[AgentRequestItem]:
    """Create a multiple agent request list."""
    return [
        AgentRequestItem(
            agent_id=201,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Security review", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=202,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Performance review", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=203,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Maintainability review", "session_id": 789},
        ),
    ]


@pytest.fixture
def sample_cache_establishing_agents() -> List[AgentRequestItem]:
    """Create agent requests for cache establishing agents."""
    return [
        AgentRequestItem(
            agent_id=301,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Security analysis", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=302,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Code maintainability analysis", "session_id": 789},
        ),
    ]


@pytest.fixture
def sample_cache_utilizing_agents() -> List[AgentRequestItem]:
    """Create agent requests for cache utilizing agents."""
    return [
        AgentRequestItem(
            agent_id=401,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Error analysis", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=402,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Performance analysis", "session_id": 789},
        ),
    ]


@pytest.fixture
def sample_mixed_agent_requests() -> List[AgentRequestItem]:
    """Create mixed agent requests (both cache establishing and utilizing)."""
    return [
        AgentRequestItem(
            agent_id=501,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Security analysis", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=502,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Error analysis", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=503,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Code maintainability analysis", "session_id": 789},
        ),
        AgentRequestItem(
            agent_id=504,
            review_id=456,
            type=RequestType.QUERY,
            payload={"content": "Performance analysis", "session_id": 789},
        ),
    ]


@pytest.fixture
def sample_user_agent_dtos_mixed() -> List[MagicMock]:
    """Create sample UserAgentDTO objects with mixed agent types."""
    user_agents = []

    # Cache establishing agents
    security_agent = MagicMock(spec=UserAgentDTO)
    security_agent.id = 501
    security_agent.agent_name = AgentTypes.SECURITY.value
    user_agents.append(security_agent)

    maintainability_agent = MagicMock(spec=UserAgentDTO)
    maintainability_agent.id = 503
    maintainability_agent.agent_name = AgentTypes.CODE_MAINTAINABILITY.value
    user_agents.append(maintainability_agent)

    # Cache utilizing agents
    error_agent = MagicMock(spec=UserAgentDTO)
    error_agent.id = 502
    error_agent.agent_name = AgentTypes.ERROR.value
    user_agents.append(error_agent)

    performance_agent = MagicMock(spec=UserAgentDTO)
    performance_agent.id = 504
    performance_agent.agent_name = AgentTypes.PERFORMANCE_OPTIMIZATION.value
    user_agents.append(performance_agent)

    return user_agents


@pytest.fixture
def sample_user_agent_dtos_cache_establishing() -> List[MagicMock]:
    """Create sample UserAgentDTO objects for cache establishing agents."""
    user_agents = []

    security_agent = MagicMock(spec=UserAgentDTO)
    security_agent.id = 301
    security_agent.agent_name = AgentTypes.SECURITY.value
    user_agents.append(security_agent)

    maintainability_agent = MagicMock(spec=UserAgentDTO)
    maintainability_agent.id = 302
    maintainability_agent.agent_name = AgentTypes.CODE_MAINTAINABILITY.value
    user_agents.append(maintainability_agent)

    return user_agents


@pytest.fixture
def sample_user_agent_dtos_cache_utilizing() -> List[MagicMock]:
    """Create sample UserAgentDTO objects for cache utilizing agents."""
    user_agents = []

    error_agent = MagicMock(spec=UserAgentDTO)
    error_agent.id = 401
    error_agent.agent_name = AgentTypes.ERROR.value
    user_agents.append(error_agent)

    performance_agent = MagicMock(spec=UserAgentDTO)
    performance_agent.id = 402
    performance_agent.agent_name = AgentTypes.PERFORMANCE_OPTIMIZATION.value
    user_agents.append(performance_agent)

    return user_agents


@pytest.fixture
def sample_local_stream_buffer() -> Dict[str, List[str]]:
    """Create a sample local stream buffer."""
    return {"test-connection-123": []}


@pytest.fixture
def sample_websocket_message_success() -> WebSocketMessage:
    """Create a sample WebSocket message for success case."""
    return WebSocketMessage(
        type="AGENT_COMPLETE",
        agent_id=101,
        data={
            "comments": [
                {
                    "line_number": 10,
                    "message": "Consider using more descriptive variable names",
                    "confidence_score": 0.8,
                }
            ],
            "summary": "Code review completed successfully",
        },
    )


@pytest.fixture
def sample_websocket_message_error() -> WebSocketMessage:
    """Create a sample WebSocket message for error case."""
    return WebSocketMessage(
        type="AGENT_ERROR", agent_id=101, data={"message": "Failed to analyze code", "error_code": "ANALYSIS_ERROR"}
    )


@pytest.fixture
def sample_websocket_message_tool_use() -> WebSocketMessage:
    """Create a sample WebSocket message for tool use request."""
    return WebSocketMessage(
        type="TOOL_USE_REQUEST",
        agent_id=101,
        data={"tool_name": "file_reader", "tool_input": {"file_path": "src/main.py", "start_line": 1, "end_line": 50}},
    )


@pytest.fixture
def sample_ide_review_response() -> Dict[str, Any]:
    """Create a sample IDE review response from IdeReviewManager."""
    return {
        "type": "REVIEW_COMPLETE",
        "status": "SUCCESS",
        "agent_id": 101,
        "data": {
            "comments": [
                {
                    "line_number": 15,
                    "message": "This function could be optimized",
                    "confidence_score": 0.9,
                    "category": "performance",
                }
            ],
            "summary": "Review completed with 1 comment",
        },
    }


@pytest.fixture
def sample_ide_review_response_error() -> Dict[str, Any]:
    """Create a sample IDE review error response from IdeReviewManager."""
    return {
        "type": "REVIEW_ERROR",
        "status": "ERROR",
        "agent_id": 101,
        "data": {"message": "Failed to process the review request", "error_details": "Invalid file format"},
    }


@pytest.fixture
def sample_ide_review_response_tool_use() -> Dict[str, Any]:
    """Create a sample IDE review response with tool use request."""
    return {
        "type": "TOOL_USE_REQUEST",
        "status": "SUCCESS",
        "agent_id": 101,
        "data": {
            "tool_name": "grep_search",
            "tool_input": {"search_path": "src/", "query": "TODO", "case_insensitive": True},
        },
    }


@pytest.fixture
def sample_connection_id() -> str:
    """Create a sample connection ID."""
    return "websocket-conn-abc123"


@pytest.fixture
def sample_review_id() -> int:
    """Create a sample review ID."""
    return 12345


@pytest.fixture
def sample_formatted_results() -> List[Dict[str, Any]]:
    """Create sample formatted results for various scenarios."""
    return [
        {"status": "ERROR", "message": "Failed to process"},
        {"type": "TOOL_USE_REQUEST", "tool_name": "file_reader"},
        {"type": "REVIEW_COMPLETE", "data": {"comments": []}},
        {"type": "REVIEW_ERROR", "error": "Processing failed"},
        {"type": "UNKNOWN_TYPE", "data": "Some data"},
        {},  # Empty result
    ]


@pytest.fixture
def sample_agent_execution_results() -> List[Dict[str, Any]]:
    """Create sample agent execution results."""
    return [
        {"agent_id": 101, "type": "REVIEW_COMPLETE", "data": {"comments": ["Comment 1"], "summary": "Success"}},
        {"agent_id": 102, "type": "TOOL_USE_REQUEST", "data": {"tool_name": "file_reader", "tool_input": {}}},
        {"agent_id": 103, "type": "REVIEW_ERROR", "data": {"message": "Failed to analyze"}},
    ]


@pytest.fixture
def sample_concurrent_agents() -> List[AgentRequestItem]:
    """Create agent requests for concurrent execution testing."""
    return [
        AgentRequestItem(
            agent_id=f"concurrent-{i}",
            type=RequestType.QUERY,
            payload={"content": f"Concurrent analysis {i}", "session_id": 789},
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_aws_websocket_manager() -> MultiAgentWebSocketManager:
    """Create a MultiAgentWebSocketManager configured for AWS (non-local)."""
    return MultiAgentWebSocketManager(connection_id="aws-websocket-conn-xyz789", review_id=67890, is_local=False)


@pytest.fixture
def sample_progress_context_data() -> Dict[str, Any]:
    """Create sample data for progress context testing."""
    return {
        "interval": 5,
        "expected_progress_messages": 3,
        "execution_duration": 15,  # seconds
    }


@pytest.fixture
def sample_error_scenarios() -> List[Dict[str, Any]]:
    """Create various error scenarios for testing."""
    return [
        {
            "error_type": "connection_error",
            "error_message": "WebSocket connection lost",
            "expected_behavior": "graceful_handling",
        },
        {
            "error_type": "agent_timeout",
            "error_message": "Agent execution timed out",
            "expected_behavior": "error_response",
        },
        {
            "error_type": "invalid_payload",
            "error_message": "Invalid request payload",
            "expected_behavior": "validation_error",
        },
        {
            "error_type": "database_error",
            "error_message": "Database connection failed",
            "expected_behavior": "retry_mechanism",
        },
    ]
