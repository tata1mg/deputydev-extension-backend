"""
Fixtures for testing ToolRequestManager.

This module provides comprehensive fixtures for testing various scenarios
of the ToolRequestManager methods including different input combinations,
mock data, and edge cases.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.comments.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)


# Mock LLM Response fixtures
@pytest.fixture
def mock_llm_response_with_tool_use() -> MagicMock:
    """Create a mock LLM response with tool use request."""
    tool_content = ToolUseRequestContent(
        tool_name="grep_search",
        tool_use_id="test_tool_use_id_123",
        tool_input={
            "query": "test_query",
            "search_path": ".",
            "case_insensitive": False,
            "use_regex": False,
            "repo_path": "/test/repo",
        },
    )

    tool_request = ToolUseRequestData(type=ContentBlockCategory.TOOL_USE_REQUEST, content=tool_content)

    response = MagicMock()
    response.parsed_content = [tool_request]
    return response


@pytest.fixture
def mock_llm_response_with_parse_final_response() -> MagicMock:
    """Create a mock LLM response with parse_final_response tool use."""
    tool_content = ToolUseRequestContent(
        tool_name="parse_final_response",
        tool_use_id="final_response_id_456",
        tool_input={
            "comments": [
                {
                    "title": "Test Comment Title",
                    "tag": "error",
                    "description": "This is a test comment description",
                    "corrective_code": "// Fixed code here",
                    "file_path": "test/file.py",
                    "line_number": 42,
                    "confidence_score": 0.9,
                    "bucket": "logic_errors",
                    "rationale": "This is the rationale for the comment",
                }
            ]
        },
    )

    tool_request = ToolUseRequestData(type=ContentBlockCategory.TOOL_USE_REQUEST, content=tool_content)

    response = MagicMock()
    response.parsed_content = [tool_request]
    return response


@pytest.fixture
def mock_llm_response_with_pr_review_planner() -> MagicMock:
    """Create a mock LLM response with pr_review_planner tool use."""
    tool_content = ToolUseRequestContent(
        tool_name="pr_review_planner",
        tool_use_id="planner_id_789",
        tool_input={"files_to_review": ["file1.py", "file2.py"], "review_strategy": "comprehensive"},
    )

    tool_request = ToolUseRequestData(type=ContentBlockCategory.TOOL_USE_REQUEST, content=tool_content)

    response = MagicMock()
    response.parsed_content = [tool_request]
    return response


@pytest.fixture
def mock_llm_response_with_text_only() -> MagicMock:
    """Create a mock LLM response with only text content."""
    text_content = TextBlockContent(text="This is just a text response")

    text_block = TextBlockData(type=ContentBlockCategory.TEXT_BLOCK, content=text_content)

    response = MagicMock()
    response.parsed_content = [text_block]
    return response


@pytest.fixture
def mock_llm_response_no_parsed_content() -> MagicMock:
    """Create a mock LLM response without parsed content."""
    response = MagicMock()
    response.parsed_content = None
    return response


@pytest.fixture
def mock_llm_response_empty_parsed_content() -> MagicMock:
    """Create a mock LLM response with empty parsed content."""
    response = MagicMock()
    response.parsed_content = []
    return response


@pytest.fixture
def mock_llm_response_without_parsed_content_attr() -> MagicMock:
    """Create a mock LLM response without parsed_content attribute."""
    response = MagicMock()
    if hasattr(response, "parsed_content"):
        delattr(response, "parsed_content")
    return response


@pytest.fixture
def mock_context_service() -> MagicMock:
    """Create a mock IdeReviewContextService."""
    context_service = MagicMock(spec=IdeReviewContextService)
    context_service.review_id = 123
    return context_service


# Tool input fixtures for various scenarios
@pytest.fixture
def valid_comments_tool_input() -> Dict[str, Any]:
    """Create valid tool input with multiple comments."""
    return {
        "comments": [
            {
                "title": "Missing Error Handling",
                "tag": "error",
                "description": "Function lacks proper error handling for edge cases",
                "corrective_code": "try:\n    # existing code\nexcept Exception as e:\n    handle_error(e)",
                "file_path": "src/utils.py",
                "line_number": 15,
                "confidence_score": 0.85,
                "bucket": "error_handling",
                "rationale": "Function could fail with invalid input",
            },
            {
                "title": "Performance Issue",
                "tag": "performance",
                "description": "Loop can be optimized using list comprehension",
                "corrective_code": "result = [process(item) for item in items if condition]",
                "file_path": "src/processing.py",
                "line_number": 25,
                "confidence_score": 0.75,
                "bucket": "performance",
                "rationale": "Current implementation is inefficient",
            },
        ]
    }


@pytest.fixture
def invalid_comments_tool_input_missing_field() -> Dict[str, Any]:
    """Create invalid tool input with missing required field."""
    return {
        "comments": [
            {
                "title": "Test Comment",
                "tag": "error",
                "description": "Test description",
                # Missing required fields like file_path, line_number, etc.
                "confidence_score": 0.8,
                "bucket": "test_bucket",
                "rationale": "Test rationale",
            }
        ]
    }


@pytest.fixture
def invalid_comments_tool_input_no_comments_array() -> Dict[str, Any]:
    """Create invalid tool input without comments array."""
    return {"no_comments": "This doesn't have comments array"}


@pytest.fixture
def comments_tool_input_with_invalid_confidence_score() -> Dict[str, Any]:
    """Create tool input with invalid confidence score."""
    return {
        "comments": [
            {
                "title": "Test Comment",
                "tag": "error",
                "description": "Test description",
                "file_path": "test.py",
                "line_number": 10,
                "confidence_score": "invalid_score",  # Should be float
                "bucket": "test_bucket",
                "rationale": "Test rationale",
            }
        ]
    }


@pytest.fixture
def multiple_tool_requests_response() -> MagicMock:
    """Create a mock LLM response with multiple tool requests."""
    tool_content_1 = ToolUseRequestContent(
        tool_name="grep_search", tool_use_id="tool_1", tool_input={"query": "search_term"}
    )

    tool_content_2 = ToolUseRequestContent(
        tool_name="file_path_searcher", tool_use_id="tool_2", tool_input={"search_terms": ["file.py"]}
    )

    tool_request_1 = ToolUseRequestData(type=ContentBlockCategory.TOOL_USE_REQUEST, content=tool_content_1)

    tool_request_2 = ToolUseRequestData(type=ContentBlockCategory.TOOL_USE_REQUEST, content=tool_content_2)

    response = MagicMock()
    response.parsed_content = [tool_request_1, tool_request_2]
    return response


@pytest.fixture
def mixed_content_response() -> MagicMock:
    """Create a mock LLM response with mixed content types."""
    text_content = TextBlockContent(text="Some text content")
    text_block = TextBlockData(type=ContentBlockCategory.TEXT_BLOCK, content=text_content)

    tool_content = ToolUseRequestContent(
        tool_name="iterative_file_reader", tool_use_id="tool_mixed", tool_input={"file_path": "test.py"}
    )

    tool_request = ToolUseRequestData(type=ContentBlockCategory.TOOL_USE_REQUEST, content=tool_content)

    response = MagicMock()
    response.parsed_content = [text_block, tool_request]
    return response


# Expected responses fixtures
@pytest.fixture
def expected_tool_request_dict() -> Dict[str, Any]:
    """Expected dictionary format for regular tool request."""
    return {
        "type": "tool_use_request",
        "tool_name": "grep_search",
        "tool_input": {
            "query": "test_query",
            "search_path": ".",
            "case_insensitive": False,
            "use_regex": False,
            "repo_path": "/test/repo",
        },
        "tool_use_id": "test_tool_use_id_123",
    }


@pytest.fixture
def expected_parsed_comments() -> List[LLMCommentData]:
    """Expected list of parsed LLMCommentData objects."""
    return [
        LLMCommentData(
            title="Missing Error Handling",
            tag="error",
            comment="Function lacks proper error handling for edge cases",
            corrective_code="try:\n    # existing code\nexcept Exception as e:\n    handle_error(e)",
            file_path="src/utils.py",
            line_number=15,
            confidence_score=0.85,
            bucket="ERROR_HANDLING",  # Formatted bucket name
            rationale="Function could fail with invalid input",
        ),
        LLMCommentData(
            title="Performance Issue",
            tag="performance",
            comment="Loop can be optimized using list comprehension",
            corrective_code="result = [process(item) for item in items if condition]",
            file_path="src/processing.py",
            line_number=25,
            confidence_score=0.75,
            bucket="PERFORMANCE",  # Formatted bucket name
            rationale="Current implementation is inefficient",
        ),
    ]


@pytest.fixture
def mock_extension_tool_handlers() -> MagicMock:
    """Mock ExtensionToolHandlers for testing."""
    mock_handlers = MagicMock()
    mock_handlers.handle_pr_review_planner = AsyncMock(return_value={"status": "success", "plan": "review_plan"})
    return mock_handlers


@pytest.fixture
def expected_review_plan_response() -> Dict[str, Any]:
    """Expected response from review planner."""
    return {"status": "success", "plan": "review_plan"}


# Invalid content block fixtures
@pytest.fixture
def mock_llm_response_with_invalid_tool_request() -> MagicMock:
    """Create a mock LLM response with invalid tool request (not ToolUseRequestData)."""
    # Create a mock object that looks like a tool request but isn't ToolUseRequestData
    invalid_tool_request = MagicMock()
    invalid_tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST
    # This will fail isinstance(content_block, ToolUseRequestData) check

    response = MagicMock()
    response.parsed_content = [invalid_tool_request]
    return response


@pytest.fixture
def session_id() -> int:
    """Sample session ID for testing."""
    return 12345
