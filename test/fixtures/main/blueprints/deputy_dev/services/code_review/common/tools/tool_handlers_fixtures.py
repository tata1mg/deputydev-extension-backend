"""
Fixtures for ToolHandlers tests.

This module provides fixtures for testing the ToolHandlers class,
including sample data, mocked objects, and test configurations.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def sample_related_code_search_input() -> Dict[str, Any]:
    """Create sample input for related code searcher."""
    return {"search_query": "authentication function implementation"}


@pytest.fixture
def sample_related_code_search_input_empty() -> Dict[str, Any]:
    """Create sample input for related code searcher with empty query."""
    return {"search_query": ""}


@pytest.fixture
def sample_related_code_search_response() -> Dict[str, Any]:
    """Create sample response for related code searcher."""
    return {
        "chunks": [
            {
                "content": "def authenticate(username, password):",
                "file_path": "src/auth.py",
                "line_number": 15,
                "relevance_score": 0.95,
            },
            {
                "content": "class AuthenticationManager:",
                "file_path": "src/auth_manager.py",
                "line_number": 8,
                "relevance_score": 0.87,
            },
        ],
        "total_chunks": 2,
    }


@pytest.fixture
def sample_grep_search_input() -> Dict[str, Any]:
    """Create sample input for grep search."""
    return {"search_path": "src/", "query": "TODO", "case_insensitive": False, "use_regex": False}


@pytest.fixture
def sample_grep_search_input_string_query() -> Dict[str, Any]:
    """Create sample input for grep search with string query."""
    return {"search_path": "src/", "query": "FIXME", "case_insensitive": True, "use_regex": False}


@pytest.fixture
def sample_grep_search_input_invalid_regex() -> Dict[str, Any]:
    """Create sample input for grep search with invalid regex."""
    return {"search_path": "src/", "query": "[invalid regex", "case_insensitive": False, "use_regex": True}


@pytest.fixture
def sample_grep_search_response() -> List[Dict[str, Any]]:
    """Create sample response for grep search."""
    mock_chunk_info = MagicMock()
    mock_chunk_info.model_dump.return_value = {"file_path": "src/main.py", "line_number": 42, "context_lines": 2}

    return [
        {"chunk_info": mock_chunk_info, "matched_line": "# TODO: Implement error handling"},
        {"chunk_info": mock_chunk_info, "matched_line": "# TODO: Add validation"},
    ]


@pytest.fixture
def sample_iterative_file_reader_input() -> Dict[str, Any]:
    """Create sample input for iterative file reader."""
    return {"file_path": "src/main.py"}


@pytest.fixture
def sample_iterative_file_reader_input_with_range() -> Dict[str, Any]:
    """Create sample input for iterative file reader with line range."""
    return {"file_path": "src/utils.py", "start_line": 10, "end_line": 50}


@pytest.fixture
def sample_iterative_file_reader_input_nonexistent() -> Dict[str, Any]:
    """Create sample input for iterative file reader with non-existent file."""
    return {"file_path": "src/nonexistent.py"}


@pytest.fixture
def sample_iterative_file_reader_response() -> MagicMock:
    """Create sample response for iterative file reader."""
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "content": "def main():\n    print('Hello World')\n    return 0",
        "start_line": 1,
        "end_line": 3,
        "total_lines": 3,
        "eof": True,
        "eof_reached": True,
    }
    return mock_response


@pytest.fixture
def sample_focused_snippets_search_input() -> Dict[str, Any]:
    """Create sample input for focused snippets searcher."""
    return {
        "search_terms": [
            {"keyword": "AuthenticationManager", "type": "class"},
            {"keyword": "validate_token", "type": "function"},
        ]
    }


@pytest.fixture
def sample_focused_snippets_search_response() -> Dict[str, Any]:
    """Create sample response for focused snippets searcher."""
    return {
        "results": [
            {
                "keyword": "AuthenticationManager",
                "type": "class",
                "definitions": [
                    {
                        "file_path": "src/auth.py",
                        "line_number": 10,
                        "content": "class AuthenticationManager:\n    def __init__(self):\n        pass",
                    }
                ],
            },
            {
                "keyword": "validate_token",
                "type": "function",
                "definitions": [
                    {
                        "file_path": "src/auth.py",
                        "line_number": 25,
                        "content": "def validate_token(token: str) -> bool:\n    return token is not None",
                    }
                ],
            },
        ]
    }


@pytest.fixture
def sample_file_path_search_input() -> Dict[str, Any]:
    """Create sample input for file path searcher."""
    return {"directory": "src/"}


@pytest.fixture
def sample_file_path_search_input_with_terms() -> Dict[str, Any]:
    """Create sample input for file path searcher with search terms."""
    return {"directory": "src/", "search_terms": ["main", "utils"]}


@pytest.fixture
def sample_file_path_search_input_invalid_dir() -> Dict[str, Any]:
    """Create sample input for file path searcher with invalid directory."""
    return {"directory": "nonexistent/"}


@pytest.fixture
def sample_file_path_search_response() -> List[str]:
    """Create sample response for file path searcher."""
    return ["src/main.py", "src/utils.py", "src/auth.py", "src/models/__init__.py", "src/models/user.py"]


@pytest.fixture
def sample_parse_final_response_input() -> Dict[str, Any]:
    """Create sample input for parse final response."""
    return {
        "comments": [
            {
                "line_number": 15,
                "message": "Consider using more descriptive variable names",
                "confidence_score": 0.8,
                "category": "maintainability",
            },
            {
                "line_number": 23,
                "message": "Add input validation for security",
                "confidence_score": 0.9,
                "category": "security",
            },
        ],
        "summary": "Found 2 issues that should be addressed",
    }


@pytest.fixture
def sample_parse_final_response_input_missing_fields() -> Dict[str, Any]:
    """Create sample input for parse final response with missing fields."""
    return {}


@pytest.fixture
def sample_pr_review_planner_input() -> Dict[str, Any]:
    """Create sample input for PR review planner."""
    return {"review_focus": "security and performance"}


@pytest.fixture
def sample_pr_review_plan() -> Dict[str, Any]:
    """Create sample PR review plan response."""
    return {
        "review_areas": [
            {
                "area": "security",
                "priority": "high",
                "specific_checks": ["Input validation", "Authentication mechanisms", "Data sanitization"],
            },
            {
                "area": "performance",
                "priority": "medium",
                "specific_checks": ["Algorithm efficiency", "Memory usage", "Database queries"],
            },
        ],
        "estimated_review_time": "30 minutes",
        "complexity_score": 7.5,
    }


@pytest.fixture
def sample_context_service() -> MagicMock:
    """Create a mock context service."""
    mock_service = MagicMock()
    mock_service.get_pr_title.return_value = "Feature: Add user authentication"
    mock_service.get_pr_description.return_value = "This PR adds JWT-based authentication system"
    mock_service.get_pr_diff.return_value = AsyncMock(return_value="+ def authenticate(user): pass")
    return mock_service


@pytest.fixture
def sample_concurrent_tool_inputs() -> List[Dict[str, Any]]:
    """Create sample inputs for concurrent tool testing."""
    return [{"comments": [f"Comment {i}"], "summary": f"Summary {i}"} for i in range(10)]


@pytest.fixture
def sample_large_tool_input() -> Dict[str, Any]:
    """Create large tool input for performance testing."""
    return {
        "comments": [
            {
                "line_number": i,
                "message": f"This is a very long comment message that contains detailed information about issue {i} "
                * 10,
                "confidence_score": 0.5 + (i % 5) * 0.1,
                "category": ["security", "performance", "maintainability", "error", "communication"][i % 5],
            }
            for i in range(100)
        ],
        "summary": "This is a comprehensive summary that covers all the major issues found in the code review. " * 50,
    }


@pytest.fixture
def sample_weaviate_client() -> MagicMock:
    """Create a mock Weaviate client."""
    mock_client = MagicMock()
    mock_client.close = MagicMock()
    return mock_client


@pytest.fixture
def sample_one_dev_review_client() -> MagicMock:
    """Create a mock OneDevReviewClient."""
    mock_client = MagicMock()
    mock_client.get_relevant_chunks = AsyncMock(return_value={"chunks": []})
    return mock_client


@pytest.fixture
def sample_embedding_manager() -> MagicMock:
    """Create a mock PRReviewEmbeddingManager."""
    mock_manager = MagicMock()
    mock_manager.get_embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return mock_manager


@pytest.fixture
def sample_review_initialisation_manager() -> MagicMock:
    """Create a mock ReviewInitialisationManager."""
    mock_manager = MagicMock()
    mock_manager.initialize = AsyncMock(return_value=True)
    return mock_manager


@pytest.fixture
def sample_process_pool_executor() -> MagicMock:
    """Create a mock ProcessPoolExecutor."""
    mock_executor = MagicMock()
    mock_executor.__enter__ = MagicMock(return_value=mock_executor)
    mock_executor.__exit__ = MagicMock(return_value=None)
    return mock_executor


@pytest.fixture
def sample_config_manager_config() -> Dict[str, Any]:
    """Create sample ConfigManager configuration."""
    return {"NUMBER_OF_WORKERS": 4, "MAX_CONCURRENT_REQUESTS": 10, "TIMEOUT_SECONDS": 30}


@pytest.fixture
def sample_llm_response_formatter() -> MagicMock:
    """Create a mock LLMResponseFormatter."""
    mock_formatter = MagicMock()
    mock_formatter.format_iterative_file_reader_response.return_value = "Formatted response content"
    return mock_formatter


@pytest.fixture
def sample_grep_search_results_empty() -> List[Dict[str, Any]]:
    """Create empty grep search results."""
    return []


@pytest.fixture
def sample_focused_snippets_empty_response() -> Dict[str, Any]:
    """Create empty focused snippets response."""
    return {"results": []}


@pytest.fixture
def sample_file_path_search_empty_response() -> List[str]:
    """Create empty file path search response."""
    return []


@pytest.fixture
def sample_error_scenarios() -> List[Dict[str, Any]]:
    """Create various error scenarios for testing."""
    return [
        {
            "error_type": "file_not_found",
            "exception": FileNotFoundError("File not found"),
            "expected_behavior": "raise_exception",
        },
        {
            "error_type": "permission_error",
            "exception": PermissionError("Permission denied"),
            "expected_behavior": "raise_exception",
        },
        {
            "error_type": "timeout_error",
            "exception": TimeoutError("Operation timed out"),
            "expected_behavior": "raise_exception",
        },
        {
            "error_type": "network_error",
            "exception": ConnectionError("Network error"),
            "expected_behavior": "raise_exception",
        },
    ]


@pytest.fixture
def sample_tool_performance_data() -> Dict[str, Any]:
    """Create performance test data for tools."""
    return {
        "small_input_size": 10,
        "medium_input_size": 100,
        "large_input_size": 1000,
        "max_execution_time": 5.0,  # seconds
        "concurrent_requests": 20,
    }


@pytest.fixture
def sample_integration_workflow_data() -> Dict[str, Any]:
    """Create integration workflow test data."""
    return {
        "workflow_steps": [
            "file_path_search",
            "iterative_file_reader",
            "grep_search",
            "focused_snippets_search",
            "related_code_search",
            "parse_final_response",
        ],
        "expected_results": {
            "file_path_search": {"data": ["file1.py", "file2.py"]},
            "iterative_file_reader": {"tool_response": "formatted_content"},
            "grep_search": {"data": []},
            "focused_snippets_search": {"results": []},
            "related_code_search": {"chunks": []},
            "parse_final_response": {"comments": [], "summary": ""},
        },
    }


@pytest.fixture
def sample_special_character_inputs() -> Dict[str, Any]:
    """Create inputs with special characters for testing."""
    return {
        "unicode_query": "查找函数 authenticate 的实现",
        "regex_special_chars": "function.*\\([^)]*\\)",
        "json_breaking_chars": '{"test": "value with \\"quotes\\""}',
        "newline_chars": "function\nwith\nnewlines",
        "emoji_chars": "🔍 Search for authentication 🔐",
    }


@pytest.fixture
def sample_boundary_conditions() -> Dict[str, Any]:
    """Create boundary condition test data."""
    return {
        "empty_strings": {"search_query": "", "file_path": "", "directory": ""},
        "very_long_strings": {
            "search_query": "x" * 10000,
            "file_path": "path/" * 1000 + "file.py",
            "directory": "dir/" * 500,
        },
        "null_values": {"search_query": None, "file_path": None, "directory": None},
    }


@pytest.fixture
def sample_async_operation_data() -> Dict[str, Any]:
    """Create data for async operation testing."""
    return {
        "operation_delays": [0.01, 0.05, 0.1, 0.5],
        "concurrent_operations": [1, 5, 10, 20],
        "timeout_values": [1, 5, 10, 30],
    }


@pytest.fixture
def sample_mocked_dependencies() -> Dict[str, MagicMock]:
    """Create all mocked dependencies in one fixture."""
    return {
        "context_value": MagicMock(
            side_effect=lambda key: {"repo_path": "/test/repo", "session_id": "test-123"}.get(key)
        ),
        "one_dev_client": MagicMock(),
        "embedding_manager": MagicMock(),
        "weaviate_client": MagicMock(),
        "init_manager": MagicMock(),
        "process_executor": MagicMock(),
        "config_manager": MagicMock(),
        "llm_formatter": MagicMock(),
    }
