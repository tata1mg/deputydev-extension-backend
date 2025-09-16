from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.backend_common.models.dto.message_thread_dto import (
    ToolUseRequestData,
    ToolUseResponseData,
)
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_request_manager import (
    ToolRequestManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.common.tools.tool_request_manager_fixtures import (
    ToolRequestManagerFixtures,
)


class TestToolRequestManager:
    """Test cases for ToolRequestManager class."""

    def test_init(self) -> None:
        """Test ToolRequestManager initialization."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)

        # Act
        manager = ToolRequestManager(context_service=mock_context_service)

        # Assert
        assert manager.context_service == mock_context_service
        assert len(manager.tools) == 5  # Expected number of tools
        assert len(manager._tool_handlers) == 7  # Expected number of handlers

    def test_get_tools(self) -> None:
        """Test get_tools returns correct list of tools."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        # Act
        tools = manager.get_tools()

        # Assert
        assert isinstance(tools, list)
        assert len(tools) == 5
        for tool in tools:
            assert isinstance(tool, ConversationTool)

    def test_get_tool_use_request_data_with_tool_requests(self) -> None:
        """Test get_tool_use_request_data with tool use requests."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_tool_requests()
        session_id = 123

        # Act
        result = manager.get_tool_use_request_data(llm_response, session_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        for request in result:
            assert isinstance(request, ToolUseRequestData)

    def test_get_tool_use_request_data_without_tool_requests(self) -> None:
        """Test get_tool_use_request_data without tool use requests."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_without_tool_requests()
        session_id = 123

        # Act
        result = manager.get_tool_use_request_data(llm_response, session_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_process_tool_use_request_success(self) -> None:
        """Test process_tool_use_request with successful tool execution."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        expected_response = ToolRequestManagerFixtures.get_sample_tool_response()

        # Mock the handler directly in the manager's _tool_handlers dict
        manager._tool_handlers["grep_search"] = AsyncMock(return_value=expected_response)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_grep_tool()
        session_id = 456

        # Act
        result = await manager.process_tool_use_request(llm_response, session_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ToolUseResponseData)
        assert result[0].content.tool_name == "grep_search"
        assert result[0].content.response == expected_response

    @pytest.mark.asyncio
    async def test_process_tool_use_request_with_exception(self) -> None:
        """Test process_tool_use_request handles exceptions gracefully."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        # Mock the handler to raise an exception
        manager._tool_handlers["grep_search"] = AsyncMock(side_effect=Exception("Tool error"))

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_grep_tool()
        session_id = 789

        # Act
        result = await manager.process_tool_use_request(llm_response, session_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ToolUseResponseData)
        assert result[0].content.tool_name == "grep_search"
        assert "Tool error" in result[0].content.response

    @pytest.mark.asyncio
    async def test_process_tool_request_with_valid_tool(self) -> None:
        """Test _process_tool_request with valid tool name."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        expected_response = ToolRequestManagerFixtures.get_sample_tool_response()

        with patch.object(manager, "_tool_handlers", {"test_tool": AsyncMock(return_value=expected_response)}):
            # Act
            result = await manager._process_tool_request("test_tool", {"input": "test"})

            # Assert
            assert result == expected_response

    @pytest.mark.asyncio
    async def test_process_tool_request_with_invalid_tool(self) -> None:
        """Test _process_tool_request with invalid tool name."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        # Act & Assert
        with pytest.raises(Exception, match="No such Tool Exists: tool_name: invalid_tool"):
            await manager._process_tool_request("invalid_tool", {"input": "test"})

    def test_is_final_response_with_parse_final_response_tool(self) -> None:
        """Test is_final_response returns True when parse_final_response tool is present."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_final_tool()

        # Act
        result = manager.is_final_response(llm_response)

        # Assert
        assert result is True

    def test_is_final_response_without_parse_final_response_tool(self) -> None:
        """Test is_final_response returns False when parse_final_response tool is not present."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_grep_tool()

        # Act
        result = manager.is_final_response(llm_response)

        # Assert
        assert result is False

    def test_is_final_response_with_no_parsed_content(self) -> None:
        """Test is_final_response returns False when no parsed content."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = Mock()
        llm_response.parsed_content = None

        # Act
        result = manager.is_final_response(llm_response)

        # Assert
        assert result is False

    def test_is_final_response_with_empty_parsed_content(self) -> None:
        """Test is_final_response returns False when parsed content is empty."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = Mock()
        llm_response.parsed_content = []

        # Act
        result = manager.is_final_response(llm_response)

        # Assert
        assert result is False

    @patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_request_manager.format_code_blocks")
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_request_manager.format_comment_bucket_name"
    )
    def test_extract_final_response_success(self, mock_format_bucket: Mock, mock_format_code: Mock) -> None:
        """Test extract_final_response successfully extracts comments."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        mock_format_code.side_effect = lambda x: f"formatted_{x}"
        mock_format_bucket.side_effect = lambda x: f"formatted_{x}"

        llm_response = ToolRequestManagerFixtures.get_mock_final_response_with_comments()

        # Act
        result = manager.extract_final_response(llm_response)

        # Assert
        assert "comments" in result
        assert isinstance(result["comments"], list)
        assert len(result["comments"]) > 0

        comment = result["comments"][0]
        assert isinstance(comment, LLMCommentData)
        assert comment.comment == "formatted_Test comment"
        assert comment.file_path == "test.py"
        assert comment.line_number == "10"
        assert comment.confidence_score == 0.8
        assert comment.bucket == "formatted_security"

    def test_extract_final_response_not_final(self) -> None:
        """Test extract_final_response returns empty dict when not final response."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_grep_tool()

        # Act
        result = manager.extract_final_response(llm_response)

        # Assert
        assert result == {}

    def test_extract_final_response_missing_comments(self) -> None:
        """Test extract_final_response raises error when comments are missing."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_final_response_without_comments()

        # Act & Assert
        with pytest.raises(ValueError, match="The parse_final_tool_response does not contain any comments array"):
            manager.extract_final_response(llm_response)

    def test_extract_final_response_invalid_comment_structure(self) -> None:
        """Test extract_final_response raises error when comment structure is invalid."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_final_response_with_invalid_comments()

        # Act & Assert
        with pytest.raises(ValueError, match="The Response does not contain the expected comment elements"):
            manager.extract_final_response(llm_response)

    @pytest.mark.asyncio
    async def test_process_tool_use_request_multiple_tools(self) -> None:
        """Test process_tool_use_request handles multiple tool requests."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        llm_response = ToolRequestManagerFixtures.get_mock_llm_response_with_multiple_tools()
        session_id = 999

        with patch.object(manager, "_process_tool_request", AsyncMock(return_value={})):
            # Act
            result = await manager.process_tool_use_request(llm_response, session_id)

            # Assert
            assert isinstance(result, list)
            assert len(result) == 2  # Two tool requests

    def test_tool_handlers_mapping_completeness(self) -> None:
        """Test that all expected tools have handlers."""
        # Arrange
        mock_context_service = Mock(spec=ContextService)
        manager = ToolRequestManager(context_service=mock_context_service)

        expected_handlers = [
            "related_code_searcher",
            "grep_search",
            "iterative_file_reader",
            "focused_snippets_searcher",
            "file_path_searcher",
            "parse_final_response",
            "pr_review_planner",
        ]

        # Act & Assert
        for handler_name in expected_handlers:
            assert handler_name in manager._tool_handlers
            assert callable(manager._tool_handlers[handler_name])
