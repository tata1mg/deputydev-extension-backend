from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler import (
    ExtensionToolHandlers,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler_fixtures import (
    ExtensionToolHandlersFixtures,
)


class TestExtensionToolHandlers:
    """Test cases for ExtensionToolHandlers class."""

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_with_comments_and_summary(self) -> None:
        """Test handle_parse_final_response with comments and summary."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_parse_final_response_input_with_data()
        expected_comments = tool_input["comments"]
        expected_summary = tool_input["summary"]

        # Act
        result = await ExtensionToolHandlers.handle_parse_final_response(tool_input)

        # Assert
        assert result["comments"] == expected_comments
        assert result["summary"] == expected_summary

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_with_empty_input(self) -> None:
        """Test handle_parse_final_response with empty input."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_empty_tool_input()

        # Act
        result = await ExtensionToolHandlers.handle_parse_final_response(tool_input)

        # Assert
        assert result["comments"] == []
        assert result["summary"] == ""

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_with_missing_keys(self) -> None:
        """Test handle_parse_final_response with missing keys."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_tool_input_missing_keys()

        # Act
        result = await ExtensionToolHandlers.handle_parse_final_response(tool_input)

        # Assert
        assert result["comments"] == []
        assert result["summary"] == ""

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_with_context_service(self) -> None:
        """Test handle_parse_final_response with context service (should be ignored)."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_parse_final_response_input_with_data()
        mock_context_service = Mock(spec=IdeReviewContextService)

        # Act
        result = await ExtensionToolHandlers.handle_parse_final_response(
            tool_input, context_service=mock_context_service
        )

        # Assert
        assert result["comments"] == tool_input["comments"]
        assert result["summary"] == tool_input["summary"]
        # Context service should not be used in this method
        mock_context_service.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler.ReviewPlanner")
    async def test_handle_pr_review_planner_success(self, mock_review_planner_class: Mock) -> None:
        """Test handle_pr_review_planner with successful execution."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_pr_review_planner_input()
        session_id = 123
        expected_diff = ExtensionToolHandlersFixtures.get_sample_pr_diff()
        expected_review_plan = ExtensionToolHandlersFixtures.get_sample_review_plan()

        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_context_service.get_pr_diff = AsyncMock(return_value=expected_diff)

        mock_review_planner_instance = Mock()
        mock_review_planner_instance.get_review_plan = AsyncMock(return_value=expected_review_plan)
        mock_review_planner_class.return_value = mock_review_planner_instance

        # Act
        result = await ExtensionToolHandlers.handle_pr_review_planner(
            tool_input, session_id, context_service=mock_context_service
        )

        # Assert
        assert result == expected_review_plan
        mock_context_service.get_pr_diff.assert_called_once_with(append_line_no_info=True)

        expected_prompt_vars = {
            "PULL_REQUEST_TITLE": "NA",
            "PULL_REQUEST_DESCRIPTION": "NA",
            "PULL_REQUEST_DIFF": expected_diff,
            "FOCUS_AREA": tool_input["review_focus"],
        }
        mock_review_planner_class.assert_called_once_with(session_id=session_id, prompt_vars=expected_prompt_vars)
        mock_review_planner_instance.get_review_plan.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler.ReviewPlanner")
    async def test_handle_pr_review_planner_without_review_focus(self, mock_review_planner_class: Mock) -> None:
        """Test handle_pr_review_planner without review_focus in input."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_tool_input_without_review_focus()
        session_id = 456
        expected_diff = ExtensionToolHandlersFixtures.get_sample_pr_diff()
        expected_review_plan = ExtensionToolHandlersFixtures.get_sample_review_plan()

        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_context_service.get_pr_diff = AsyncMock(return_value=expected_diff)

        mock_review_planner_instance = Mock()
        mock_review_planner_instance.get_review_plan = AsyncMock(return_value=expected_review_plan)
        mock_review_planner_class.return_value = mock_review_planner_instance

        # Act
        result = await ExtensionToolHandlers.handle_pr_review_planner(
            tool_input, session_id, context_service=mock_context_service
        )

        # Assert
        assert result == expected_review_plan
        expected_prompt_vars = {
            "PULL_REQUEST_TITLE": "NA",
            "PULL_REQUEST_DESCRIPTION": "NA",
            "PULL_REQUEST_DIFF": expected_diff,
            "FOCUS_AREA": "",
        }
        mock_review_planner_class.assert_called_once_with(session_id=session_id, prompt_vars=expected_prompt_vars)

    @pytest.mark.asyncio
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler.ReviewPlanner")
    async def test_handle_pr_review_planner_context_service_error(self, mock_review_planner_class: Mock) -> None:
        """Test handle_pr_review_planner when context service raises error."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_pr_review_planner_input()
        session_id = 789

        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_context_service.get_pr_diff = AsyncMock(side_effect=Exception("Cache error"))

        # Act & Assert
        with pytest.raises(Exception, match="Cache error"):
            await ExtensionToolHandlers.handle_pr_review_planner(
                tool_input, session_id, context_service=mock_context_service
            )

        mock_context_service.get_pr_diff.assert_called_once_with(append_line_no_info=True)
        mock_review_planner_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler.ReviewPlanner")
    async def test_handle_pr_review_planner_review_planner_error(self, mock_review_planner_class: Mock) -> None:
        """Test handle_pr_review_planner when ReviewPlanner raises error."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_pr_review_planner_input()
        session_id = 999
        expected_diff = ExtensionToolHandlersFixtures.get_sample_pr_diff()

        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_context_service.get_pr_diff = AsyncMock(return_value=expected_diff)

        mock_review_planner_instance = Mock()
        mock_review_planner_instance.get_review_plan = AsyncMock(side_effect=Exception("Review planner error"))
        mock_review_planner_class.return_value = mock_review_planner_instance

        # Act & Assert
        with pytest.raises(Exception, match="Review planner error"):
            await ExtensionToolHandlers.handle_pr_review_planner(
                tool_input, session_id, context_service=mock_context_service
            )

        mock_review_planner_instance.get_review_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_preserves_original_data_types(self) -> None:
        """Test handle_parse_final_response preserves original data types."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_parse_final_response_with_complex_data()

        # Act
        result = await ExtensionToolHandlers.handle_parse_final_response(tool_input)

        # Assert
        assert result["comments"] == tool_input["comments"]
        assert result["summary"] == tool_input["summary"]
        assert isinstance(result["comments"], list)
        assert isinstance(result["summary"], str)

    @pytest.mark.asyncio
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler.ReviewPlanner")
    async def test_handle_pr_review_planner_prompt_vars_structure(self, mock_review_planner_class: Mock) -> None:
        """Test handle_pr_review_planner creates correct prompt_vars structure."""
        # Arrange
        tool_input = ExtensionToolHandlersFixtures.get_pr_review_planner_input()
        session_id = 111
        expected_diff = ExtensionToolHandlersFixtures.get_sample_pr_diff()

        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_context_service.get_pr_diff = AsyncMock(return_value=expected_diff)

        mock_review_planner_instance = Mock()
        mock_review_planner_instance.get_review_plan = AsyncMock(return_value={})
        mock_review_planner_class.return_value = mock_review_planner_instance

        # Act
        await ExtensionToolHandlers.handle_pr_review_planner(
            tool_input, session_id, context_service=mock_context_service
        )

        # Assert
        call_args = mock_review_planner_class.call_args
        prompt_vars = call_args.kwargs["prompt_vars"]

        assert "PULL_REQUEST_TITLE" in prompt_vars
        assert "PULL_REQUEST_DESCRIPTION" in prompt_vars
        assert "PULL_REQUEST_DIFF" in prompt_vars
        assert "FOCUS_AREA" in prompt_vars

        assert prompt_vars["PULL_REQUEST_TITLE"] == "NA"
        assert prompt_vars["PULL_REQUEST_DESCRIPTION"] == "NA"
        assert prompt_vars["PULL_REQUEST_DIFF"] == expected_diff
        assert prompt_vars["FOCUS_AREA"] == tool_input["review_focus"]
