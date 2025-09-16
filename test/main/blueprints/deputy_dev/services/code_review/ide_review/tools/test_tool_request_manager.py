"""
Unit tests for ToolRequestManager.

This module provides comprehensive unit tests for the ToolRequestManager class,
covering all methods including get_tools, parse_tool_use_request, is_final_response,
is_review_planner_response, extract_final_response, process_review_planner_response,
and _parse_comments_from_tool_input with various scenarios including edge cases and error handling.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.backend_common.services.llm.dataclasses.main import ConversationTool
from app.main.blueprints.deputy_dev.services.code_review.ide_review.comments.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager import (
    ToolRequestManager,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager_fixtures import *


class TestToolRequestManagerInitialization:
    """Test cases for ToolRequestManager initialization."""

    def test_init_with_valid_context_service(self, mock_context_service: MagicMock) -> None:
        """Test ToolRequestManager initialization with valid context service."""
        manager = ToolRequestManager(mock_context_service)

        assert manager.context_service == mock_context_service
        assert len(manager.tools) == 5

        # Verify tools are correctly initialized
        tool_names = [tool.name for tool in manager.tools]
        expected_tools = [
            "grep_search",
            "iterative_file_reader",
            "file_path_searcher",
            "parse_final_response",
            "pr_review_planner",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names


class TestToolRequestManagerGetTools:
    """Test cases for ToolRequestManager.get_tools method."""

    def test_get_tools_returns_correct_list(self, mock_context_service: MagicMock) -> None:
        """Test get_tools returns the correct list of ConversationTool objects."""
        manager = ToolRequestManager(mock_context_service)
        tools = manager.get_tools()

        assert isinstance(tools, list)
        assert len(tools) == 5

        for tool in tools:
            assert isinstance(tool, ConversationTool)
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "input_schema")

    def test_get_tools_returns_same_instance(self, mock_context_service: MagicMock) -> None:
        """Test get_tools returns the same tools instance each time."""
        manager = ToolRequestManager(mock_context_service)
        tools1 = manager.get_tools()
        tools2 = manager.get_tools()

        assert tools1 is tools2


class TestToolRequestManagerParseToolUseRequest:
    """Test cases for ToolRequestManager.parse_tool_use_request method."""

    def test_parse_tool_use_request_regular_tool_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_tool_use: MagicMock,
        expected_tool_request_dict: Dict[str, Any],
    ) -> None:
        """Test parsing regular tool use request successfully."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_with_tool_use)

        assert result == expected_tool_request_dict

    def test_parse_tool_use_request_special_tool_parse_final_response(
        self, mock_context_service: MagicMock, mock_llm_response_with_parse_final_response: MagicMock
    ) -> None:
        """Test parsing special tool parse_final_response returns None."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_with_parse_final_response)

        assert result is None

    def test_parse_tool_use_request_special_tool_pr_review_planner(
        self, mock_context_service: MagicMock, mock_llm_response_with_pr_review_planner: MagicMock
    ) -> None:
        """Test parsing special tool pr_review_planner returns None."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_with_pr_review_planner)

        assert result is None

    def test_parse_tool_use_request_no_parsed_content(
        self, mock_context_service: MagicMock, mock_llm_response_no_parsed_content: MagicMock
    ) -> None:
        """Test parsing when response has no parsed content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_no_parsed_content)

        assert result is None

    def test_parse_tool_use_request_empty_parsed_content(
        self, mock_context_service: MagicMock, mock_llm_response_empty_parsed_content: MagicMock
    ) -> None:
        """Test parsing when response has empty parsed content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_empty_parsed_content)

        assert result is None

    def test_parse_tool_use_request_without_parsed_content_attr(
        self, mock_context_service: MagicMock, mock_llm_response_without_parsed_content_attr: MagicMock
    ) -> None:
        """Test parsing when response doesn't have parsed_content attribute."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_without_parsed_content_attr)

        assert result is None

    def test_parse_tool_use_request_text_only_content(
        self, mock_context_service: MagicMock, mock_llm_response_with_text_only: MagicMock
    ) -> None:
        """Test parsing when response has only text content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_with_text_only)

        assert result is None

    def test_parse_tool_use_request_invalid_tool_request_type(
        self, mock_context_service: MagicMock, mock_llm_response_with_invalid_tool_request: MagicMock
    ) -> None:
        """Test parsing with invalid tool request type (not ToolUseRequestData)."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mock_llm_response_with_invalid_tool_request)

        assert result is None

    def test_parse_tool_use_request_multiple_tools_returns_first_regular(
        self, mock_context_service: MagicMock, multiple_tool_requests_response: MagicMock
    ) -> None:
        """Test parsing returns first regular tool when multiple tools present."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(multiple_tool_requests_response)

        assert result is not None
        assert result["tool_name"] == "grep_search"
        assert result["tool_use_id"] == "tool_1"

    def test_parse_tool_use_request_mixed_content(
        self, mock_context_service: MagicMock, mixed_content_response: MagicMock
    ) -> None:
        """Test parsing with mixed content types returns tool request."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.parse_tool_use_request(mixed_content_response)

        assert result is not None
        assert result["tool_name"] == "iterative_file_reader"
        assert result["tool_use_id"] == "tool_mixed"


class TestToolRequestManagerIsFinalResponse:
    """Test cases for ToolRequestManager.is_final_response method."""

    def test_is_final_response_true(
        self, mock_context_service: MagicMock, mock_llm_response_with_parse_final_response: MagicMock
    ) -> None:
        """Test is_final_response returns True for parse_final_response tool."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_final_response(mock_llm_response_with_parse_final_response)

        assert result is True

    def test_is_final_response_false_regular_tool(
        self, mock_context_service: MagicMock, mock_llm_response_with_tool_use: MagicMock
    ) -> None:
        """Test is_final_response returns False for regular tool."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_final_response(mock_llm_response_with_tool_use)

        assert result is False

    def test_is_final_response_false_no_parsed_content(
        self, mock_context_service: MagicMock, mock_llm_response_no_parsed_content: MagicMock
    ) -> None:
        """Test is_final_response returns False when no parsed content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_final_response(mock_llm_response_no_parsed_content)

        assert result is False

    def test_is_final_response_false_text_only(
        self, mock_context_service: MagicMock, mock_llm_response_with_text_only: MagicMock
    ) -> None:
        """Test is_final_response returns False for text-only content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_final_response(mock_llm_response_with_text_only)

        assert result is False


class TestToolRequestManagerIsReviewPlannerResponse:
    """Test cases for ToolRequestManager.is_review_planner_response method."""

    def test_is_review_planner_response_true(
        self, mock_context_service: MagicMock, mock_llm_response_with_pr_review_planner: MagicMock
    ) -> None:
        """Test is_review_planner_response returns True for pr_review_planner tool."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_review_planner_response(mock_llm_response_with_pr_review_planner)

        assert result is True

    def test_is_review_planner_response_false_regular_tool(
        self, mock_context_service: MagicMock, mock_llm_response_with_tool_use: MagicMock
    ) -> None:
        """Test is_review_planner_response returns False for regular tool."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_review_planner_response(mock_llm_response_with_tool_use)

        assert result is False

    def test_is_review_planner_response_false_final_response(
        self, mock_context_service: MagicMock, mock_llm_response_with_parse_final_response: MagicMock
    ) -> None:
        """Test is_review_planner_response returns False for final response tool."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_review_planner_response(mock_llm_response_with_parse_final_response)

        assert result is False

    def test_is_review_planner_response_false_no_parsed_content(
        self, mock_context_service: MagicMock, mock_llm_response_no_parsed_content: MagicMock
    ) -> None:
        """Test is_review_planner_response returns False when no parsed content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.is_review_planner_response(mock_llm_response_no_parsed_content)

        assert result is False


class TestToolRequestManagerExtractFinalResponse:
    """Test cases for ToolRequestManager.extract_final_response method."""

    def test_extract_final_response_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_parse_final_response: MagicMock,
        expected_parsed_comments: List[LLMCommentData],
    ) -> None:
        """Test successful extraction of final response with valid comments."""
        manager = ToolRequestManager(mock_context_service)

        # Update the mock to have valid tool input
        tool_input = {
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
        }
        mock_llm_response_with_parse_final_response.parsed_content[0].content.tool_input = tool_input

        result = manager.extract_final_response(mock_llm_response_with_parse_final_response)

        assert "comments" in result
        assert isinstance(result["comments"], list)
        assert len(result["comments"]) == 1

        comment = result["comments"][0]
        assert isinstance(comment, LLMCommentData)
        assert comment.title == "Test Comment Title"
        assert comment.tag == "error"
        assert comment.comment == "This is a test comment description"
        assert comment.file_path == "test/file.py"
        assert comment.line_number == 42
        assert comment.confidence_score == 0.9
        assert comment.bucket == "LOGIC_ERRORS"  # Formatted bucket name

    def test_extract_final_response_not_final_response(
        self, mock_context_service: MagicMock, mock_llm_response_with_tool_use: MagicMock
    ) -> None:
        """Test extraction returns empty dict when not final response."""
        manager = ToolRequestManager(mock_context_service)
        result = manager.extract_final_response(mock_llm_response_with_tool_use)

        assert result == {}

    def test_extract_final_response_missing_comments_array(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_parse_final_response: MagicMock,
        invalid_comments_tool_input_no_comments_array: Dict[str, Any],
    ) -> None:
        """Test extraction raises ValueError when comments array is missing."""
        manager = ToolRequestManager(mock_context_service)

        # Update mock to have invalid tool input
        mock_llm_response_with_parse_final_response.parsed_content[
            0
        ].content.tool_input = invalid_comments_tool_input_no_comments_array

        with pytest.raises(ValueError, match="The parse_final_tool_response does not contain any comments array"):
            manager.extract_final_response(mock_llm_response_with_parse_final_response)

    def test_extract_final_response_missing_required_field(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_parse_final_response: MagicMock,
        invalid_comments_tool_input_missing_field: Dict[str, Any],
    ) -> None:
        """Test extraction raises ValueError when required field is missing."""
        manager = ToolRequestManager(mock_context_service)

        # Update mock to have invalid tool input
        mock_llm_response_with_parse_final_response.parsed_content[
            0
        ].content.tool_input = invalid_comments_tool_input_missing_field

        with pytest.raises(ValueError, match="The comment is missing required field"):
            manager.extract_final_response(mock_llm_response_with_parse_final_response)

    def test_extract_final_response_invalid_confidence_score_logs_warning(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_parse_final_response: MagicMock,
        comments_tool_input_with_invalid_confidence_score: Dict[str, Any],
    ) -> None:
        """Test extraction logs warning and skips comment with invalid confidence score."""
        manager = ToolRequestManager(mock_context_service)

        # Update mock to have invalid confidence score
        mock_llm_response_with_parse_final_response.parsed_content[
            0
        ].content.tool_input = comments_tool_input_with_invalid_confidence_score

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager.AppLogger.log_warn"
        ) as mock_log_warn:
            result = manager.extract_final_response(mock_llm_response_with_parse_final_response)

            # Should return empty comments list since invalid comment was skipped
            assert result == {"comments": []}
            mock_log_warn.assert_called_once()

    def test_extract_final_response_multiple_comments(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_parse_final_response: MagicMock,
        valid_comments_tool_input: Dict[str, Any],
    ) -> None:
        """Test extraction with multiple valid comments."""
        manager = ToolRequestManager(mock_context_service)

        # Update mock to have multiple comments
        mock_llm_response_with_parse_final_response.parsed_content[0].content.tool_input = valid_comments_tool_input

        result = manager.extract_final_response(mock_llm_response_with_parse_final_response)

        assert "comments" in result
        assert len(result["comments"]) == 2

        # Verify both comments are parsed correctly
        comment1 = result["comments"][0]
        assert comment1.title == "Missing Error Handling"
        assert comment1.file_path == "src/utils.py"

        comment2 = result["comments"][1]
        assert comment2.title == "Performance Issue"
        assert comment2.file_path == "src/processing.py"


class TestToolRequestManagerProcessReviewPlannerResponse:
    """Test cases for ToolRequestManager.process_review_planner_response method."""

    @pytest.mark.asyncio
    async def test_process_review_planner_response_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_response_with_pr_review_planner: MagicMock,
        session_id: int,
        expected_review_plan_response: Dict[str, Any],
    ) -> None:
        """Test successful processing of review planner response."""
        manager = ToolRequestManager(mock_context_service)

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager.ExtensionToolHandlers"
        ) as mock_handlers:
            mock_handlers.handle_pr_review_planner = AsyncMock(return_value=expected_review_plan_response)

            result = await manager.process_review_planner_response(mock_llm_response_with_pr_review_planner, session_id)

            assert result == expected_review_plan_response
            mock_handlers.handle_pr_review_planner.assert_called_once_with(
                {"files_to_review": ["file1.py", "file2.py"], "review_strategy": "comprehensive"},
                session_id,
                mock_context_service,
            )

    @pytest.mark.asyncio
    async def test_process_review_planner_response_not_planner_response(
        self, mock_context_service: MagicMock, mock_llm_response_with_tool_use: MagicMock, session_id: int
    ) -> None:
        """Test processing returns None when not a planner response."""
        manager = ToolRequestManager(mock_context_service)

        result = await manager.process_review_planner_response(mock_llm_response_with_tool_use, session_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_process_review_planner_response_no_parsed_content(
        self, mock_context_service: MagicMock, mock_llm_response_no_parsed_content: MagicMock, session_id: int
    ) -> None:
        """Test processing returns None when no parsed content."""
        manager = ToolRequestManager(mock_context_service)

        result = await manager.process_review_planner_response(mock_llm_response_no_parsed_content, session_id)

        assert result is None


class TestToolRequestManagerPrivateHasToolUse:
    """Test cases for ToolRequestManager._has_tool_use private method."""

    def test_has_tool_use_found(
        self, mock_context_service: MagicMock, mock_llm_response_with_parse_final_response: MagicMock
    ) -> None:
        """Test _has_tool_use returns True when tool is found."""
        manager = ToolRequestManager(mock_context_service)
        result = manager._has_tool_use(mock_llm_response_with_parse_final_response, "parse_final_response")

        assert result is True

    def test_has_tool_use_not_found(
        self, mock_context_service: MagicMock, mock_llm_response_with_tool_use: MagicMock
    ) -> None:
        """Test _has_tool_use returns False when tool is not found."""
        manager = ToolRequestManager(mock_context_service)
        result = manager._has_tool_use(mock_llm_response_with_tool_use, "parse_final_response")

        assert result is False

    def test_has_tool_use_no_parsed_content(
        self, mock_context_service: MagicMock, mock_llm_response_no_parsed_content: MagicMock
    ) -> None:
        """Test _has_tool_use returns False when no parsed content."""
        manager = ToolRequestManager(mock_context_service)
        result = manager._has_tool_use(mock_llm_response_no_parsed_content, "any_tool")

        assert result is False

    def test_has_tool_use_wrong_tool_name(
        self, mock_context_service: MagicMock, mock_llm_response_with_pr_review_planner: MagicMock
    ) -> None:
        """Test _has_tool_use returns False for wrong tool name."""
        manager = ToolRequestManager(mock_context_service)
        result = manager._has_tool_use(mock_llm_response_with_pr_review_planner, "parse_final_response")

        assert result is False


class TestToolRequestManagerPrivateParseCommentsFromToolInput:
    """Test cases for ToolRequestManager._parse_comments_from_tool_input private method."""

    def test_parse_comments_from_tool_input_success(
        self, mock_context_service: MagicMock, valid_comments_tool_input: Dict[str, Any]
    ) -> None:
        """Test successful parsing of comments from tool input."""
        manager = ToolRequestManager(mock_context_service)
        result = manager._parse_comments_from_tool_input(valid_comments_tool_input)

        assert "comments" in result
        assert len(result["comments"]) == 2

        # Verify first comment
        comment1 = result["comments"][0]
        assert comment1.title == "Missing Error Handling"
        assert comment1.tag == "error"
        assert comment1.confidence_score == 0.85
        assert comment1.bucket == "ERROR_HANDLING"  # Formatted bucket name

        # Verify second comment
        comment2 = result["comments"][1]
        assert comment2.title == "Performance Issue"
        assert comment2.tag == "performance"
        assert comment2.confidence_score == 0.75
        assert comment2.bucket == "PERFORMANCE"  # Formatted bucket name

    def test_parse_comments_from_tool_input_no_comments_array(
        self, mock_context_service: MagicMock, invalid_comments_tool_input_no_comments_array: Dict[str, Any]
    ) -> None:
        """Test parsing raises ValueError when comments array is missing."""
        manager = ToolRequestManager(mock_context_service)

        with pytest.raises(ValueError, match="The parse_final_tool_response does not contain any comments array"):
            manager._parse_comments_from_tool_input(invalid_comments_tool_input_no_comments_array)

    def test_parse_comments_from_tool_input_missing_required_field(
        self, mock_context_service: MagicMock, invalid_comments_tool_input_missing_field: Dict[str, Any]
    ) -> None:
        """Test parsing raises ValueError for missing required field."""
        manager = ToolRequestManager(mock_context_service)

        with pytest.raises(ValueError, match="The comment is missing required field"):
            manager._parse_comments_from_tool_input(invalid_comments_tool_input_missing_field)

    def test_parse_comments_from_tool_input_logs_warning_on_validation_error(
        self, mock_context_service: MagicMock, comments_tool_input_with_invalid_confidence_score: Dict[str, Any]
    ) -> None:
        """Test parsing logs warning and skips invalid comments."""
        manager = ToolRequestManager(mock_context_service)

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager.AppLogger.log_warn"
        ) as mock_log_warn:
            result = manager._parse_comments_from_tool_input(comments_tool_input_with_invalid_confidence_score)

            # Should return empty list since invalid comment was skipped
            assert result == {"comments": []}
            mock_log_warn.assert_called_once()

    def test_parse_comments_from_tool_input_handles_none_corrective_code(self, mock_context_service: MagicMock) -> None:
        """Test parsing handles None corrective_code correctly."""
        manager = ToolRequestManager(mock_context_service)

        tool_input = {
            "comments": [
                {
                    "title": "Test Comment",
                    "tag": "error",
                    "description": "Test description",
                    "corrective_code": None,  # None value
                    "file_path": "test.py",
                    "line_number": 10,
                    "confidence_score": 0.8,
                    "bucket": "test_bucket",
                    "rationale": "Test rationale",
                }
            ]
        }

        result = manager._parse_comments_from_tool_input(tool_input)

        assert len(result["comments"]) == 1
        comment = result["comments"][0]
        assert comment.corrective_code is None

    def test_parse_comments_from_tool_input_formats_code_blocks(self, mock_context_service: MagicMock) -> None:
        """Test parsing applies code block formatting to description."""
        manager = ToolRequestManager(mock_context_service)

        tool_input = {
            "comments": [
                {
                    "title": "Test Comment",
                    "tag": "error",
                    "description": "```python\nprint('test')\n```",
                    "file_path": "test.py",
                    "line_number": 10,
                    "confidence_score": 0.8,
                    "bucket": "test_bucket",
                    "rationale": "Test rationale",
                }
            ]
        }

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager.format_code_blocks"
        ) as mock_format:
            mock_format.return_value = "formatted_code"

            result = manager._parse_comments_from_tool_input(tool_input)

            mock_format.assert_called_once_with("```python\nprint('test')\n```")
            assert result["comments"][0].comment == "formatted_code"

    def test_parse_comments_from_tool_input_formats_bucket_name(self, mock_context_service: MagicMock) -> None:
        """Test parsing applies bucket name formatting."""
        manager = ToolRequestManager(mock_context_service)

        tool_input = {
            "comments": [
                {
                    "title": "Test Comment",
                    "tag": "error",
                    "description": "Test description",
                    "file_path": "test.py",
                    "line_number": 10,
                    "confidence_score": 0.8,
                    "bucket": "error_handling",
                    "rationale": "Test rationale",
                }
            ]
        }

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager.format_comment_bucket_name"
        ) as mock_format:
            mock_format.return_value = "ERROR_HANDLING"

            result = manager._parse_comments_from_tool_input(tool_input)

            mock_format.assert_called_once_with("error_handling")
            assert result["comments"][0].bucket == "ERROR_HANDLING"


class TestToolRequestManagerEdgeCases:
    """Test cases for edge cases and error scenarios."""

    def test_manager_handles_missing_attributes_gracefully(self, mock_context_service: MagicMock) -> None:
        """Test manager handles missing attributes gracefully."""
        manager = ToolRequestManager(mock_context_service)

        # Create a mock response with missing attributes
        malformed_response = MagicMock()
        malformed_response.parsed_content = [MagicMock()]

        # Should not raise exception, should return None
        result = manager.parse_tool_use_request(malformed_response)
        assert result is None

    def test_manager_handles_empty_tool_input(self, mock_context_service: MagicMock) -> None:
        """Test manager handles empty tool input."""
        manager = ToolRequestManager(mock_context_service)

        empty_tool_input = {"comments": []}
        result = manager._parse_comments_from_tool_input(empty_tool_input)

        assert result == {"comments": []}

    def test_manager_handles_none_values_in_comments(self, mock_context_service: MagicMock) -> None:
        """Test manager handles None values in comment fields gracefully."""
        manager = ToolRequestManager(mock_context_service)

        tool_input = {
            "comments": [
                {
                    "title": None,  # This should cause validation error
                    "tag": "error",
                    "description": "Test description",
                    "file_path": "test.py",
                    "line_number": 10,
                    "confidence_score": 0.8,
                    "bucket": "test_bucket",
                    "rationale": "Test rationale",
                }
            ]
        }

        with pytest.raises(ValueError, match="The comment is missing required field"):
            manager._parse_comments_from_tool_input(tool_input)
