from typing import Any, Dict, List
from unittest.mock import Mock

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    ToolUseRequestContent,
    ToolUseRequestData,
)
from app.backend_common.services.llm.dataclasses.main import NonStreamingParsedLLMCallResponse


class ToolRequestManagerFixtures:
    """Fixtures for ToolRequestManager tests."""

    @staticmethod
    def get_mock_llm_response_with_tool_requests() -> NonStreamingParsedLLMCallResponse:
        """Return mock LLM response with tool requests."""
        tool_request = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="grep_search",
                tool_use_id="tool_123",
                tool_input={"query": "test query", "file_pattern": "*.py"},
            )
        )
        tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = [tool_request]
        return response

    @staticmethod
    def get_mock_llm_response_without_tool_requests() -> NonStreamingParsedLLMCallResponse:
        """Return mock LLM response without tool requests."""
        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = []
        return response

    @staticmethod
    def get_mock_llm_response_with_grep_tool() -> NonStreamingParsedLLMCallResponse:
        """Return mock LLM response with grep search tool."""
        tool_request = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="grep_search", tool_use_id="grep_456", tool_input={"query": "function", "path": "src/"}
            )
        )
        tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = [tool_request]
        return response

    @staticmethod
    def get_mock_llm_response_with_final_tool() -> Mock:
        """Return mock LLM response with parse_final_response tool."""
        tool_request = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="parse_final_response",
                tool_use_id="final_789",
                tool_input={"comments": [], "summary": "Review complete"},
            )
        )
        tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock()
        response.parsed_content = [tool_request]
        return response

    @staticmethod
    def get_mock_llm_response_with_multiple_tools() -> NonStreamingParsedLLMCallResponse:
        """Return mock LLM response with multiple tool requests."""
        tool_request1 = ToolUseRequestData(
            content=ToolUseRequestContent(tool_name="grep_search", tool_use_id="tool_1", tool_input={"query": "test"})
        )
        tool_request1.type = ContentBlockCategory.TOOL_USE_REQUEST

        tool_request2 = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="file_path_searcher", tool_use_id="tool_2", tool_input={"pattern": "*.py"}
            )
        )
        tool_request2.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = [tool_request1, tool_request2]
        return response

    @staticmethod
    def get_sample_tool_response() -> Dict[str, Any]:
        """Return sample tool response."""
        return {
            "results": [
                {"file": "test.py", "line": 10, "content": "def test_function():"},
                {"file": "main.py", "line": 5, "content": "import os"},
            ],
            "total_matches": 2,
        }

    @staticmethod
    def get_mock_final_response_with_comments() -> NonStreamingParsedLLMCallResponse:
        """Return mock final response with valid comments."""
        tool_request = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="parse_final_response",
                tool_use_id="final_comments",
                tool_input={
                    "comments": [
                        {
                            "description": "Test comment",
                            "corrective_code": "# Fixed code",
                            "file_path": "test.py",
                            "line_number": "10",
                            "confidence_score": 0.8,
                            "bucket": "security",
                            "rationale": "Security issue found",
                        }
                    ],
                    "summary": "Review completed",
                },
            )
        )
        tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = [tool_request]
        return response

    @staticmethod
    def get_mock_final_response_without_comments() -> NonStreamingParsedLLMCallResponse:
        """Return mock final response without comments."""
        tool_request = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="parse_final_response",
                tool_use_id="final_no_comments",
                tool_input={"summary": "Review completed"},
            )
        )
        tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = [tool_request]
        return response

    @staticmethod
    def get_mock_final_response_with_invalid_comments() -> NonStreamingParsedLLMCallResponse:
        """Return mock final response with invalid comment structure."""
        tool_request = ToolUseRequestData(
            content=ToolUseRequestContent(
                tool_name="parse_final_response",
                tool_use_id="final_invalid",
                tool_input={
                    "comments": [
                        {
                            "description": "Test comment",
                            # Missing required fields
                        }
                    ],
                    "summary": "Review completed",
                },
            )
        )
        tool_request.type = ContentBlockCategory.TOOL_USE_REQUEST

        response = Mock(spec=NonStreamingParsedLLMCallResponse)
        response.parsed_content = [tool_request]
        return response

    @staticmethod
    def get_complete_comment_data() -> Dict[str, Any]:
        """Return complete comment data structure."""
        return {
            "description": "This function needs better error handling",
            "corrective_code": "try:\n    result = risky_operation()\nexcept Exception as e:\n    handle_error(e)",
            "file_path": "src/main.py",
            "line_number": 25,
            "confidence_score": 0.9,
            "bucket": "error_handling",
            "rationale": "Function lacks proper exception handling for potential failures",
        }

    @staticmethod
    def get_minimal_comment_data() -> Dict[str, Any]:
        """Return minimal comment data structure."""
        return {
            "description": "Simple comment",
            "corrective_code": None,
            "file_path": "test.py",
            "line_number": 1,
            "confidence_score": 0.5,
            "bucket": "style",
            "rationale": "Minor style issue",
        }

    @staticmethod
    def get_various_tool_inputs() -> List[Dict[str, Any]]:
        """Return various tool input examples."""
        return [
            {"query": "function", "path": "src/"},
            {"pattern": "*.py", "exclude": ["__pycache__"]},
            {"file_path": "main.py", "start_line": 1, "end_line": 50},
            {"search_term": "class", "case_sensitive": True},
            {"comments": [], "summary": "No issues found"},
        ]

    @staticmethod
    def get_tool_names() -> List[str]:
        """Return list of expected tool names."""
        return [
            "related_code_searcher",
            "grep_search",
            "iterative_file_reader",
            "focused_snippets_searcher",
            "file_path_searcher",
            "parse_final_response",
            "pr_review_planner",
        ]

    @staticmethod
    def get_session_ids() -> List[int]:
        """Return list of session IDs for testing."""
        return [1, 123, 456, 789, 999, 0, -1, 9999999]
