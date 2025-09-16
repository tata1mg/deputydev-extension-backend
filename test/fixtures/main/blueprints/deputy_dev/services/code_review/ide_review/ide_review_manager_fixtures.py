"""
Fixtures for testing IdeReviewManager.

This module provides comprehensive fixtures for testing various scenarios
of the IdeReviewManager methods including different input combinations,
mock data, and edge cases.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    RequestType,
    ToolUseResponseData,
)


# AgentRequestItem fixtures
@pytest.fixture
def sample_agent_request_query() -> AgentRequestItem:
    """Create a sample AgentRequestItem for query type."""
    return AgentRequestItem(agent_id=1, review_id=100, type=RequestType.QUERY, tool_use_response=None)


@pytest.fixture
def sample_agent_request_tool_use_response() -> AgentRequestItem:
    """Create a sample AgentRequestItem for tool use response type."""
    tool_use_response = ToolUseResponseData(
        tool_name="test_tool", tool_use_id="tool_123", response={"status": "success", "data": "test_data"}
    )

    return AgentRequestItem(
        agent_id=1, review_id=100, type=RequestType.TOOL_USE_RESPONSE, tool_use_response=tool_use_response
    )


# Repository DTOs fixtures
@pytest.fixture
def sample_extension_review_dto() -> MagicMock:
    """Create a sample extension review DTO."""
    dto = MagicMock()
    dto.id = 100
    dto.session_id = "session_123"
    dto.review_status = "IN_PROGRESS"
    dto.repo_id = 50
    return dto


@pytest.fixture
def sample_user_agent_dto() -> MagicMock:
    """Create a sample user agent DTO."""
    dto = MagicMock()
    dto.id = 1
    dto.agent_name = "security"
    dto.display_name = "Security Agent"
    dto.confidence_score = 0.9
    dto.custom_prompt = "Review this code thoroughly"
    dto.exclusions = ["test_files"]
    dto.inclusions = ["src_files"]
    dto.objective = "Find bugs and improvements"
    dto.is_custom_agent = False
    return dto


@pytest.fixture
def sample_user_agent_dto_valid_agent() -> MagicMock:
    """Create a sample user agent DTO with valid agent name."""
    dto = MagicMock()
    dto.agent_name = "security"  # Valid agent type
    return dto


@pytest.fixture
def sample_user_agent_dto_invalid_agent() -> MagicMock:
    """Create a sample user agent DTO with invalid agent name."""
    dto = MagicMock()
    dto.agent_name = "invalid_agent_type"
    return dto


@pytest.fixture
def sample_user_agent_dto_none_agent() -> MagicMock:
    """Create a sample user agent DTO with None agent name."""
    dto = MagicMock()
    dto.agent_name = None
    return dto


# AgentAndInitParams fixtures
@pytest.fixture
def sample_agent_and_init_params() -> AgentAndInitParams:
    """Create a sample AgentAndInitParams."""
    return AgentAndInitParams(agent_type=AgentTypes.SECURITY)


@pytest.fixture
def expected_agent_and_init_params() -> AgentAndInitParams:
    """Create expected AgentAndInitParams for testing."""
    return AgentAndInitParams(agent_type=AgentTypes.SECURITY)


# AgentRunResult fixtures
@pytest.fixture
def sample_agent_run_result_success() -> AgentRunResult:
    """Create a sample AgentRunResult with success status."""
    result = MagicMock()
    result.agent_result = {"status": "success"}
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_error() -> AgentRunResult:
    """Create a sample AgentRunResult with error status."""
    result = MagicMock()
    result.agent_result = {"status": "error", "message": "Processing failed"}
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_tool_use() -> AgentRunResult:
    """Create a sample AgentRunResult with tool use request."""
    result = MagicMock()
    result.agent_result = {
        "type": "tool_use_request",
        "tool_name": "file_reader",
        "tool_input": {"file_path": "/test/file.py"},
        "tool_use_id": "tool_456",
    }
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_non_dict() -> AgentRunResult:
    """Create a sample AgentRunResult with non-dict result."""
    result = MagicMock()
    result.agent_result = "string_result"
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_unknown() -> AgentRunResult:
    """Create a sample AgentRunResult with unknown type/status."""
    result = MagicMock()
    result.agent_result = {"type": "unknown_type", "status": "unknown_status"}
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_with_comments() -> AgentRunResult:
    """Create a sample AgentRunResult with comments for bucket name testing."""
    # Mock comment objects
    comment1 = MagicMock()
    comment1.bucket = "original_bucket_1"
    comment2 = MagicMock()
    comment2.bucket = "original_bucket_2"

    result = MagicMock()
    result.agent_result = {"comments": [comment1, comment2]}
    result.display_name = "Test Agent Name"
    return result


@pytest.fixture
def sample_agent_run_result_empty_comments() -> AgentRunResult:
    """Create a sample AgentRunResult with empty comments list."""
    result = MagicMock()
    result.agent_result = {"comments": []}
    result.display_name = "Test Agent"
    return result


# Comment DTO fixtures
@pytest.fixture
def sample_comment_dto() -> MagicMock:
    """Create a sample comment DTO."""
    dto = MagicMock()
    dto.id = 1
    dto.file_path = "src/models/user.py"
    dto.line_number = 25
    dto.title = "Performance Issue"
    dto.comment = "This loop can be optimized using list comprehension"
    dto.corrective_code = None
    dto.rationale = None
    return dto


@pytest.fixture
def sample_comment_dto_with_optional_fields() -> MagicMock:
    """Create a sample comment DTO with optional fields."""
    dto = MagicMock()
    dto.id = 1
    dto.file_path = "src/models/user.py"
    dto.line_number = 25
    dto.title = "Performance Issue"
    dto.comment = "This loop can be optimized using list comprehension"
    dto.corrective_code = "users = [u for u in all_users if u.is_active]"
    dto.rationale = "List comprehension is more pythonic and efficient"
    return dto


# Expected response fixtures
@pytest.fixture
def expected_query_response() -> Dict[str, Any]:
    """Create expected response for query request."""
    return {
        "type": "AGENT_COMPLETE",
        "agent_id": 1,
    }


@pytest.fixture
def expected_tool_use_response() -> Dict[str, Any]:
    """Create expected response for tool use request."""
    return {
        "type": "TOOL_USE_REQUEST",
        "data": {
            "tool_name": "file_reader",
            "tool_input": {"file_path": "/test/file.py"},
            "tool_use_id": "tool_456",
        },
        "agent_id": 1,
    }


@pytest.fixture
def expected_success_response() -> Dict[str, Any]:
    """Create expected response for success status."""
    return {
        "type": "AGENT_COMPLETE",
        "agent_id": 1,
    }


@pytest.fixture
def expected_error_response() -> Dict[str, Any]:
    """Create expected response for error status."""
    return {
        "type": "AGENT_FAIL",
        "data": {"message": "Processing failed"},
        "agent_id": 1,
    }


@pytest.fixture
def expected_comment_fix_query() -> str:
    """Create expected comment fix query."""
    return "Performance Issue This loop can be optimized using list comprehension"


@pytest.fixture
def expected_cancel_success_response() -> Dict[str, str]:
    """Create expected response for successful review cancellation."""
    return {"status": "Cancelled", "message": "Review cancelled successfully"}


# Scenario-based fixtures
@pytest.fixture
def multiple_agent_request_scenarios() -> List[Dict[str, Any]]:
    """Create multiple agent request scenarios for comprehensive testing."""
    return [
        {
            "name": "query_request",
            "request": AgentRequestItem(agent_id=1, review_id=100, type=RequestType.QUERY),
            "expected_status_insert": True,
        },
        {
            "name": "tool_use_response_request",
            "request": AgentRequestItem(
                agent_id=2,
                review_id=101,
                type=RequestType.TOOL_USE_RESPONSE,
                tool_use_response=ToolUseResponseData(
                    tool_name="test_tool", tool_use_id="tool_789", response={"result": "test"}
                ),
            ),
            "expected_status_insert": False,
        },
        {
            "name": "tool_use_failed_request",
            "request": AgentRequestItem(agent_id=3, review_id=102, type=RequestType.TOOL_USE_FAILED),
            "expected_status_insert": False,
        },
    ]


@pytest.fixture
def agent_result_format_scenarios() -> List[Dict[str, Any]]:
    """Create agent result format scenarios for testing."""
    return [
        {
            "name": "tool_use_request_format",
            "result": {
                "type": "tool_use_request",
                "tool_name": "code_analyzer",
                "tool_input": {"code": "def test(): pass"},
                "tool_use_id": "tool_999",
            },
            "expected_type": "TOOL_USE_REQUEST",
        },
        {"name": "success_status_format", "result": {"status": "success"}, "expected_type": "AGENT_COMPLETE"},
        {
            "name": "error_status_format",
            "result": {"status": "error", "message": "Custom error message"},
            "expected_type": "AGENT_FAIL",
        },
        {"name": "unknown_format", "result": {"type": "unknown", "status": "unknown"}, "expected_type": None},
    ]


@pytest.fixture
def agent_name_validation_scenarios() -> List[Dict[str, Any]]:
    """Create agent name validation scenarios for testing."""
    return [
        {"name": "valid_code_reviewer", "agent_name": "code_reviewer", "should_succeed": True},
        {"name": "invalid_agent_name", "agent_name": "non_existent_agent", "should_succeed": False},
        {"name": "none_agent_name", "agent_name": None, "should_succeed": False},
        {"name": "empty_agent_name", "agent_name": "", "should_succeed": False},
    ]


# Error scenario fixtures
@pytest.fixture
def database_error_scenarios() -> List[Dict[str, Any]]:
    """Create database error scenarios for testing."""
    return [
        {
            "name": "extension_review_not_found",
            "error_location": "extension_reviews_repo",
            "error_type": "not_found",
            "error_message": "Extension review not found",
        },
        {
            "name": "user_agent_not_found",
            "error_location": "user_agent_repo",
            "error_type": "not_found",
            "error_message": "User agent not found",
        },
        {
            "name": "status_insert_failure",
            "error_location": "status_repo",
            "error_type": "insert_error",
            "error_message": "Failed to insert agent status",
        },
        {
            "name": "comment_not_found",
            "error_location": "comment_repo",
            "error_type": "not_found",
            "error_message": "Comment not found",
        },
    ]


# Mock factory fixtures
@pytest.fixture
def mock_repository_factory() -> Dict[str, MagicMock]:
    """Create factory for repository mocks."""
    return {
        "extension_reviews": MagicMock(),
        "user_agent": MagicMock(),
        "review_agent_status": MagicMock(),
        "ide_comment": MagicMock(),
    }


@pytest.fixture
def mock_service_factory() -> Dict[str, MagicMock]:
    """Create factory for service mocks."""
    return {
        "context_service": MagicMock(),
        "llm_handler": MagicMock(),
        "agent_factory": MagicMock(),
        "prompt_feature_factory": MagicMock(),
    }


# Integration test fixtures
@pytest.fixture
def complete_review_diff_setup() -> Dict[str, Any]:
    """Create complete setup for review_diff integration testing."""
    return {
        "agent_request": AgentRequestItem(agent_id=1, review_id=100, type=RequestType.QUERY),
        "extension_review": MagicMock(id=100, session_id="session_123"),
        "user_agent": MagicMock(id=1, agent_name="code_reviewer", display_name="Code Reviewer", confidence_score=0.9),
        "agent_result": MagicMock(agent_result={"status": "success"}, display_name="Code Reviewer"),
        "expected_response": {"type": "AGENT_COMPLETE", "agent_id": 1},
    }


# Performance test fixtures
@pytest.fixture
def large_agent_result_with_many_comments() -> AgentRunResult:
    """Create agent result with many comments for performance testing."""
    comments = []
    for i in range(100):
        comment = MagicMock()
        comment.bucket = f"original_bucket_{i}"
        comments.append(comment)

    result = MagicMock()
    result.agent_result = {"comments": comments}
    result.display_name = "Performance Test Agent"
    return result


# Additional AgentRequestItem fixtures
@pytest.fixture
def sample_agent_request_tool_use_failed() -> AgentRequestItem:
    """Create a sample AgentRequestItem for tool use failed type."""
    return AgentRequestItem(agent_id=1, review_id=100, type=RequestType.TOOL_USE_FAILED, tool_use_response=None)


# Additional User Agent DTO fixtures
@pytest.fixture
def sample_user_agent_dto_custom() -> MagicMock:
    """Create a sample user agent DTO with custom agent settings."""
    dto = MagicMock()
    dto.id = 1
    dto.agent_name = "security"
    dto.display_name = "Custom Security Agent"
    dto.confidence_score = 0.8
    dto.custom_prompt = "Custom security review instructions"
    dto.exclusions = ["test_files", "docs"]
    dto.inclusions = ["src_files", "core"]
    dto.objective = "Find security vulnerabilities"
    dto.is_custom_agent = True
    return dto


@pytest.fixture
def sample_user_agent_dto_exception() -> MagicMock:
    """Create a sample user agent DTO that raises exception when accessing agent_name."""
    dto = MagicMock()
    dto.agent_name = MagicMock(side_effect=Exception("Agent name access failed"))
    return dto


# Additional AgentRunResult fixtures
@pytest.fixture
def sample_agent_run_result_partial_tool_use() -> AgentRunResult:
    """Create a sample AgentRunResult with partial tool use data."""
    result = MagicMock()
    result.agent_result = {
        "type": "tool_use_request",
        "tool_name": "incomplete_tool",
        "tool_input": {},  # Present but empty
        "tool_use_id": "tool_partial_123",
    }
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_nested_error() -> AgentRunResult:
    """Create a sample AgentRunResult with nested error message."""
    result = MagicMock()
    result.agent_result = {
        "status": "error",
        "error": {
            "code": "PROCESSING_FAILED",
            "message": "Nested error occurred",
            "details": {"reason": "Invalid input"},
        },
    }
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_with_extra_fields() -> AgentRunResult:
    """Create a sample AgentRunResult with extra fields."""
    result = MagicMock()
    result.agent_result = {"status": "success", "extra_field": "should_be_ignored", "internal_data": {"debug": "info"}}
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_empty_dict() -> AgentRunResult:
    """Create a sample AgentRunResult with empty dictionary."""
    result = MagicMock()
    result.agent_result = {}
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_mixed_case_status() -> AgentRunResult:
    """Create a sample AgentRunResult with mixed case status."""
    result = MagicMock()
    result.agent_result = {"status": "Success"}  # Capital S
    result.display_name = "Test Agent"
    return result


@pytest.fixture
def sample_agent_run_result_special_chars_display_name() -> AgentRunResult:
    """Create a sample AgentRunResult with special characters in display name."""
    comment1 = MagicMock()
    comment1.bucket = "original_bucket_1"
    comment2 = MagicMock()
    comment2.bucket = "original_bucket_2"

    result = MagicMock()
    result.agent_result = {"comments": [comment1, comment2]}
    result.display_name = "Test-Agent@#$ Name!"
    return result


@pytest.fixture
def sample_agent_run_result_unicode_display_name() -> AgentRunResult:
    """Create a sample AgentRunResult with unicode characters in display name."""
    comment1 = MagicMock()
    comment1.bucket = "original_bucket_1"

    result = MagicMock()
    result.agent_result = {"comments": [comment1]}
    result.display_name = "測試 Agent Naïve Résumé"
    return result


@pytest.fixture
def sample_agent_run_result_single_word_display_name() -> AgentRunResult:
    """Create a sample AgentRunResult with single word display name."""
    comment1 = MagicMock()
    comment1.bucket = "original_bucket_1"

    result = MagicMock()
    result.agent_result = {"comments": [comment1]}
    result.display_name = "SecurityAgent"
    return result


@pytest.fixture
def sample_agent_run_result_large_tool_input() -> AgentRunResult:
    """Create a sample AgentRunResult with large tool input data."""
    large_input = {"code": "def function():\n    pass\n" * 1000}  # Large code input
    result = MagicMock()
    result.agent_result = {
        "type": "tool_use_request",
        "tool_name": "code_analyzer",
        "tool_input": large_input,
        "tool_use_id": "tool_large_123",
    }
    result.display_name = "Test Agent"
    return result


# Additional Comment DTO fixtures
@pytest.fixture
def sample_comment_dto_very_long() -> MagicMock:
    """Create a sample comment DTO with very long content."""
    dto = MagicMock()
    dto.id = 1
    dto.file_path = "src/models/user.py"
    dto.line_number = 25
    dto.title = "Performance Issue " * 50  # Very long title
    dto.comment = "This is a very long comment that explains in detail " * 20  # Very long comment
    dto.corrective_code = "def optimized_function():\n    pass\n" * 10  # Long corrective code
    dto.rationale = "The rationale for this change is extensive " * 15  # Long rationale
    return dto


# Additional Extension Review DTO fixtures
@pytest.fixture
def sample_extension_review_dto_cancelled() -> MagicMock:
    """Create a sample extension review DTO that is already cancelled."""
    dto = MagicMock()
    dto.id = 100
    dto.session_id = "session_123"
    dto.review_status = "Cancelled"
    dto.repo_id = 50
    return dto


# Expected response fixtures for new tests
@pytest.fixture
def expected_nested_error_response() -> Dict[str, Any]:
    """Create expected response for nested error."""
    return {
        "type": "AGENT_FAIL",
        "data": {"message": "An error occurred"},  # Default message since nested error doesn't have direct message
        "agent_id": 1,
    }


# Scenario-based fixtures for advanced testing
@pytest.fixture
def all_valid_agent_types_scenarios() -> List[Dict[str, Any]]:
    """Create scenarios for all valid agent types."""
    return [
        {"agent_name": "security", "should_succeed": True},
        {"agent_name": "code_communication", "should_succeed": True},
        {"agent_name": "performance_optimisation", "should_succeed": True},
        {"agent_name": "code_maintainability", "should_succeed": True},
        {"agent_name": "error", "should_succeed": True},
        {"agent_name": "invalid_agent", "should_succeed": False},
        {"agent_name": "", "should_succeed": False},
    ]


@pytest.fixture
def case_sensitive_agent_scenarios() -> List[Dict[str, Any]]:
    """Create case sensitivity scenarios for agents."""
    return [
        {"agent_name": "security", "should_succeed": True},
        {"agent_name": "Security", "should_succeed": False},  # Case sensitive
        {"agent_name": "SECURITY", "should_succeed": False},  # Case sensitive
        {"agent_name": "code_communication", "should_succeed": True},
        {"agent_name": "Code_Communication", "should_succeed": False},  # Case sensitive
    ]


# Edge case fixtures
@pytest.fixture
def edge_case_comment_scenarios() -> List[Dict[str, Any]]:
    """Create edge case scenarios for comment processing."""
    return [
        {
            "name": "comment_with_special_characters",
            "comment": MagicMock(
                file_path="src/models/user@#$.py",
                line_number=1,
                title="Special chars: @#$%^&*()",
                comment="Comment with 'quotes' and \"double quotes\"",
                corrective_code=None,
                rationale=None,
            ),
        },
        {
            "name": "comment_with_very_long_text",
            "comment": MagicMock(
                file_path="src/models/user.py",
                line_number=999999,
                title="x" * 500,  # Very long title
                comment="y" * 1000,  # Very long comment
                corrective_code="z" * 200,  # Long corrective code
                rationale="a" * 300,  # Long rationale
            ),
        },
        {
            "name": "comment_with_multiline_content",
            "comment": MagicMock(
                file_path="src/models/user.py",
                line_number=25,
                title="Multi-line\nTitle\nWith\nBreaks",
                comment="Multi-line\ncomment\nwith\nline\nbreaks",
                corrective_code="def func():\n    return True\n",
                rationale="Multi-line\nrationale\ntext",
            ),
        },
    ]
