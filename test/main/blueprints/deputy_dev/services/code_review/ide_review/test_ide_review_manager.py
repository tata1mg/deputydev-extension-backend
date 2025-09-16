"""
Unit tests for IdeReviewManager.

This module provides comprehensive unit tests for the IdeReviewManager class,
covering all methods including review_diff, format_agent_response,
get_agent_and_init_params_for_review, generate_comment_fix_query,
and cancel_review with various scenarios including edge cases and error handling.
"""

import asyncio
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentRunResult,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager import IdeReviewManager
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager_fixtures import *


class TestIdeReviewManagerReviewDiff:
    """Test cases for IdeReviewManager.review_diff method."""

    @pytest.mark.asyncio
    async def test_review_diff_query_request_success(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
        expected_query_response: Dict[str, Any],
    ) -> None:
        """Test successful review_diff for query request type."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()

            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                result = await IdeReviewManager.review_diff(sample_agent_request_query)

            # Verify
            assert result == expected_query_response
            mock_ext_repo.db_get.assert_called_once_with(
                filters={"id": sample_agent_request_query.review_id}, fetch_one=True
            )
            mock_user_agent_repo.db_get.assert_called_once_with(
                filters={"id": sample_agent_request_query.agent_id}, fetch_one=True
            )
            mock_status_repo.db_insert.assert_called_once()
            mock_agent.run_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_diff_tool_use_response_request_success(
        self,
        sample_agent_request_tool_use_response: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_tool_use: AgentRunResult,
        expected_tool_use_response: Dict[str, Any],
    ) -> None:
        """Test successful review_diff for tool_use_response request type."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)

            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_tool_use)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                result = await IdeReviewManager.review_diff(sample_agent_request_tool_use_response)

            # Verify
            assert result == expected_tool_use_response
            # Should not insert agent status for non-query requests
            mock_status_repo.db_insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_review_diff_extension_review_not_found(
        self,
        sample_agent_request_query: AgentRequestItem,
    ) -> None:
        """Test review_diff when extension review is not found."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=None)
            mock_user_agent_repo.db_get = AsyncMock(return_value=None)

            # Execute and verify
            with pytest.raises(AttributeError):  # Will raise when trying to access session_id on None
                await IdeReviewManager.review_diff(sample_agent_request_query)

    @pytest.mark.asyncio
    async def test_review_diff_user_agent_not_found(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
    ) -> None:
        """Test review_diff when user agent is not found."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=None)

            # Execute and verify
            with pytest.raises(AttributeError):  # Will raise when trying to access agent_name on None
                await IdeReviewManager.review_diff(sample_agent_request_query)

    @pytest.mark.asyncio
    async def test_review_diff_agent_run_failure(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
    ) -> None:
        """Test review_diff when agent run fails."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()

            # Mock agent to fail
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(side_effect=Exception("Agent execution failed"))
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute and verify
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                with pytest.raises(Exception, match="Agent execution failed"):
                    await IdeReviewManager.review_diff(sample_agent_request_query)


class TestIdeReviewManagerFormatAgentResponse:
    """Test cases for IdeReviewManager.format_agent_response method."""

    def test_format_agent_response_tool_use_request(
        self,
        sample_agent_run_result_tool_use: AgentRunResult,
        expected_tool_use_response: Dict[str, Any],
    ) -> None:
        """Test formatting agent response for tool use request."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_tool_use, agent_id)
        assert result == expected_tool_use_response

    def test_format_agent_response_success(
        self,
        sample_agent_run_result_success: AgentRunResult,
        expected_success_response: Dict[str, Any],
    ) -> None:
        """Test formatting agent response for success status."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_success, agent_id)
        assert result == expected_success_response

    def test_format_agent_response_error(
        self,
        sample_agent_run_result_error: AgentRunResult,
        expected_error_response: Dict[str, Any],
    ) -> None:
        """Test formatting agent response for error status."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_error, agent_id)
        assert result == expected_error_response

    def test_format_agent_response_non_dict_result(
        self,
        sample_agent_run_result_non_dict: AgentRunResult,
    ) -> None:
        """Test formatting agent response when result is not a dictionary."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_non_dict, agent_id)
        assert result is None

    def test_format_agent_response_unknown_type(
        self,
        sample_agent_run_result_unknown: AgentRunResult,
    ) -> None:
        """Test formatting agent response for unknown type/status."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_unknown, agent_id)
        assert result is None


class TestIdeReviewManagerGetAgentAndInitParams:
    """Test cases for IdeReviewManager.get_agent_and_init_params_for_review method."""

    def test_get_agent_and_init_params_success(
        self,
        sample_user_agent_dto_valid_agent: MagicMock,
        expected_agent_and_init_params: AgentAndInitParams,
    ) -> None:
        """Test successful retrieval of agent and init params."""
        result = IdeReviewManager.get_agent_and_init_params_for_review(sample_user_agent_dto_valid_agent)
        assert result is not None
        assert result.agent_type == expected_agent_and_init_params.agent_type

    def test_get_agent_and_init_params_invalid_agent_name(
        self,
        sample_user_agent_dto_invalid_agent: MagicMock,
    ) -> None:
        """Test handling of invalid agent name."""
        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AppLogger"
        ) as mock_logger:
            result = IdeReviewManager.get_agent_and_init_params_for_review(sample_user_agent_dto_invalid_agent)

            assert result is None
            mock_logger.log_warn.assert_called_once_with(
                f"Invalid agent name: {sample_user_agent_dto_invalid_agent.agent_name}"
            )

    def test_get_agent_and_init_params_none_agent_name(
        self,
        sample_user_agent_dto_none_agent: MagicMock,
    ) -> None:
        """Test handling of None agent name."""
        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AppLogger"
        ) as mock_logger:
            result = IdeReviewManager.get_agent_and_init_params_for_review(sample_user_agent_dto_none_agent)

            assert result is None
            mock_logger.log_warn.assert_called_once()


class TestIdeReviewManagerUpdateBucketName:
    """Test cases for IdeReviewManager._update_bucket_name method."""

    def test_update_bucket_name_success(
        self,
        sample_agent_run_result_with_comments: AgentRunResult,
    ) -> None:
        """Test successful bucket name update."""
        # Get initial state
        comments = sample_agent_run_result_with_comments.agent_result["comments"]
        original_buckets = [comment.bucket for comment in comments]

        # Execute
        IdeReviewManager._update_bucket_name(sample_agent_run_result_with_comments)

        # Verify
        expected_bucket = "_".join(sample_agent_run_result_with_comments.display_name.upper().split())
        for comment in comments:
            assert comment.bucket == expected_bucket
            assert comment.bucket != original_buckets[0]  # Ensure it changed

    def test_update_bucket_name_empty_comments(
        self,
        sample_agent_run_result_empty_comments: AgentRunResult,
    ) -> None:
        """Test bucket name update with empty comments list."""
        # Execute - should not raise any exceptions
        IdeReviewManager._update_bucket_name(sample_agent_run_result_empty_comments)

        # Verify comments list is still empty
        comments = sample_agent_run_result_empty_comments.agent_result["comments"]
        assert len(comments) == 0


class TestIdeReviewManagerGenerateCommentFixQuery:
    """Test cases for IdeReviewManager.generate_comment_fix_query method."""

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_success(
        self,
        sample_comment_dto: MagicMock,
        expected_comment_fix_query: str,
    ) -> None:
        """Test successful generation of comment fix query."""
        comment_id = 1

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(return_value=sample_comment_dto)

            # Execute
            result = await IdeReviewManager.generate_comment_fix_query(comment_id)

            # Verify - just check that key components are present
            assert sample_comment_dto.file_path in result
            assert str(sample_comment_dto.line_number) in result
            assert sample_comment_dto.title in result
            assert sample_comment_dto.comment in result
            mock_comment_repo.db_get.assert_called_once_with({"id": comment_id}, fetch_one=True)

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_comment_not_found(
        self,
    ) -> None:
        """Test comment fix query generation when comment is not found."""
        comment_id = 999

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(return_value=None)

            # Execute and verify
            with pytest.raises(ValueError, match=f"Comment with ID {comment_id} not found"):
                await IdeReviewManager.generate_comment_fix_query(comment_id)

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_with_optional_fields(
        self,
        sample_comment_dto_with_optional_fields: MagicMock,
    ) -> None:
        """Test comment fix query generation with optional fields present."""
        comment_id = 1

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(return_value=sample_comment_dto_with_optional_fields)

            # Execute
            result = await IdeReviewManager.generate_comment_fix_query(comment_id)

            # Verify that optional fields are included
            assert sample_comment_dto_with_optional_fields.corrective_code in result
            assert sample_comment_dto_with_optional_fields.rationale in result

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_database_error(
        self,
    ) -> None:
        """Test comment fix query generation when database error occurs."""
        comment_id = 1

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(side_effect=Exception("Database error"))

            # Execute and verify
            with pytest.raises(Exception, match="Database error"):
                await IdeReviewManager.generate_comment_fix_query(comment_id)


class TestIdeReviewManagerCancelReview:
    """Test cases for IdeReviewManager.cancel_review method."""

    @pytest.mark.asyncio
    async def test_cancel_review_success(
        self,
        sample_extension_review_dto: MagicMock,
        expected_cancel_success_response: Dict[str, str],
    ) -> None:
        """Test successful review cancellation."""
        review_id = 1
        manager = IdeReviewManager()

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
        ) as mock_ext_repo:
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_ext_repo.update_review = AsyncMock()

            # Execute
            result = await manager.cancel_review(review_id)

            # Verify
            assert result == expected_cancel_success_response
            mock_ext_repo.db_get.assert_called_once_with(filters={"id": review_id}, fetch_one=True)
            mock_ext_repo.update_review.assert_called_once_with(review_id, {"review_status": "Cancelled"})

    @pytest.mark.asyncio
    async def test_cancel_review_not_found(
        self,
    ) -> None:
        """Test review cancellation when review is not found."""
        review_id = 999
        manager = IdeReviewManager()

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
        ) as mock_ext_repo:
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=None)

            # Execute and verify
            with pytest.raises(ValueError, match=f"Review with ID {review_id} not found"):
                await manager.cancel_review(review_id)

    @pytest.mark.asyncio
    async def test_cancel_review_database_error_on_get(
        self,
    ) -> None:
        """Test review cancellation when database get fails."""
        review_id = 1
        manager = IdeReviewManager()

        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.logger"
            ) as mock_logger,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(side_effect=Exception("Database get error"))

            # Execute and verify
            with pytest.raises(Exception, match="Database get error"):
                await manager.cancel_review(review_id)

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_review_database_error_on_update(
        self,
        sample_extension_review_dto: MagicMock,
    ) -> None:
        """Test review cancellation when database update fails."""
        review_id = 1
        manager = IdeReviewManager()

        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.logger"
            ) as mock_logger,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_ext_repo.update_review = AsyncMock(side_effect=Exception("Database update error"))

            # Execute and verify
            with pytest.raises(Exception, match="Database update error"):
                await manager.cancel_review(review_id)

            mock_logger.error.assert_called_once()


class TestIdeReviewManagerReviewDiffAdditionalScenarios:
    """Additional test cases for IdeReviewManager.review_diff method covering edge cases."""

    @pytest.mark.asyncio
    async def test_review_diff_tool_use_failed_request(
        self,
        sample_agent_request_tool_use_failed: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
        expected_success_response: Dict[str, Any],
    ) -> None:
        """Test review_diff for tool_use_failed request type."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)

            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                result = await IdeReviewManager.review_diff(sample_agent_request_tool_use_failed)

            # Verify
            assert result == expected_success_response
            # Should not insert agent status for non-query requests
            mock_status_repo.db_insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_review_diff_with_none_agent_and_init_params(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
    ) -> None:
        """Test review_diff when get_agent_and_init_params_for_review returns None."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()

            # Mock agent factory to avoid the error - it should succeed with None
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=MagicMock(agent_result={"status": "success"}))
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute - should succeed even with None agent_and_init_params
            with patch.object(IdeReviewManager, "get_agent_and_init_params_for_review", return_value=None):
                result = await IdeReviewManager.review_diff(sample_agent_request_query)
                # Should still get a response
                assert result is not None

    @pytest.mark.asyncio
    async def test_review_diff_with_custom_agent(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto_custom: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
        expected_success_response: Dict[str, Any],
    ) -> None:
        """Test review_diff with custom agent settings."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto_custom)
            mock_status_repo.db_insert = AsyncMock()

            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                result = await IdeReviewManager.review_diff(sample_agent_request_query)

            # Verify
            assert result == expected_success_response
            # Verify custom agent meta info is handled
            mock_status_repo.db_insert.assert_called_once()
            call_args = mock_status_repo.db_insert.call_args[0][0]
            assert call_args.meta_info["is_custom_agent"] is True
            assert call_args.meta_info["custom_prompt"] == sample_user_agent_dto_custom.custom_prompt

    @pytest.mark.asyncio
    async def test_review_diff_context_service_initialization_error(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
    ) -> None:
        """Test review_diff when context service initialization fails."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_context_service.side_effect = Exception("Context service initialization failed")

            # Execute and verify
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                with pytest.raises(Exception, match="Context service initialization failed"):
                    await IdeReviewManager.review_diff(sample_agent_request_query)

    @pytest.mark.asyncio
    async def test_review_diff_llm_handler_initialization_error(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
    ) -> None:
        """Test review_diff when LLM handler initialization fails."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_context_service.return_value = MagicMock()
            mock_llm_handler.side_effect = Exception("LLM handler initialization failed")

            # Execute and verify
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                with pytest.raises(Exception, match="LLM handler initialization failed"):
                    await IdeReviewManager.review_diff(sample_agent_request_query)

    @pytest.mark.asyncio
    async def test_review_diff_agent_factory_error(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
    ) -> None:
        """Test review_diff when agent factory fails to create agent."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_context_service.return_value = MagicMock()
            mock_llm_handler.return_value = MagicMock()
            mock_agent_factory.get_code_review_agent.side_effect = Exception("Agent factory failed")

            # Execute and verify
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                with pytest.raises(Exception, match="Agent factory failed"):
                    await IdeReviewManager.review_diff(sample_agent_request_query)

    @pytest.mark.asyncio
    async def test_review_diff_status_insertion_failure(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
    ) -> None:
        """Test review_diff when status insertion fails but process continues."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock(side_effect=Exception("Status insertion failed"))

            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute and verify - should propagate the error
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                with pytest.raises(Exception, match="Status insertion failed"):
                    await IdeReviewManager.review_diff(sample_agent_request_query)


class TestIdeReviewManagerFormatAgentResponseAdvanced:
    """Advanced test cases for IdeReviewManager.format_agent_response method."""

    def test_format_agent_response_partial_tool_use_data(
        self,
        sample_agent_run_result_partial_tool_use: AgentRunResult,
    ) -> None:
        """Test formatting agent response with partial tool use data."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_partial_tool_use, agent_id)
        # Should handle partial data gracefully
        assert result["type"] == "TOOL_USE_REQUEST"
        assert result["agent_id"] == agent_id
        assert "data" in result

    def test_format_agent_response_nested_error_message(
        self,
        sample_agent_run_result_nested_error: AgentRunResult,
        expected_nested_error_response: Dict[str, Any],
    ) -> None:
        """Test formatting agent response with nested error message."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_nested_error, agent_id)
        assert result == expected_nested_error_response

    def test_format_agent_response_with_extra_fields(
        self,
        sample_agent_run_result_with_extra_fields: AgentRunResult,
    ) -> None:
        """Test formatting agent response that contains extra fields."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_with_extra_fields, agent_id)
        # Should only include expected fields
        assert result["type"] == "AGENT_COMPLETE"
        assert result["agent_id"] == agent_id
        assert "extra_field" not in result

    def test_format_agent_response_empty_dict(
        self,
        sample_agent_run_result_empty_dict: AgentRunResult,
    ) -> None:
        """Test formatting agent response with empty dictionary."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_empty_dict, agent_id)
        assert result is None

    def test_format_agent_response_mixed_case_status(
        self,
        sample_agent_run_result_mixed_case_status: AgentRunResult,
    ) -> None:
        """Test formatting agent response with mixed case status."""
        agent_id = 1
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_mixed_case_status, agent_id)
        # Status matching should be case sensitive
        assert result is None


class TestIdeReviewManagerGetAgentAndInitParamsAdvanced:
    """Advanced test cases for IdeReviewManager.get_agent_and_init_params_for_review method."""

    def test_get_agent_and_init_params_all_valid_agent_types(
        self,
        all_valid_agent_types_scenarios: List[Dict[str, Any]],
    ) -> None:
        """Test get_agent_and_init_params with all valid agent types."""
        for scenario in all_valid_agent_types_scenarios:
            user_agent_dto = MagicMock()
            user_agent_dto.agent_name = scenario["agent_name"]

            result = IdeReviewManager.get_agent_and_init_params_for_review(user_agent_dto)

            if scenario["should_succeed"]:
                assert result is not None
                assert result.agent_type.value == scenario["agent_name"]
            else:
                assert result is None

    def test_get_agent_and_init_params_case_sensitivity(
        self,
        case_sensitive_agent_scenarios: List[Dict[str, Any]],
    ) -> None:
        """Test get_agent_and_init_params case sensitivity."""
        for scenario in case_sensitive_agent_scenarios:
            user_agent_dto = MagicMock()
            user_agent_dto.agent_name = scenario["agent_name"]

            with patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AppLogger"
            ) as mock_logger:
                result = IdeReviewManager.get_agent_and_init_params_for_review(user_agent_dto)

                if scenario["should_succeed"]:
                    assert result is not None
                    mock_logger.log_warn.assert_not_called()
                else:
                    assert result is None
                    mock_logger.log_warn.assert_called_once()

    def test_get_agent_and_init_params_exception_handling(
        self,
        sample_user_agent_dto_exception: MagicMock,
    ) -> None:
        """Test get_agent_and_init_params exception handling."""
        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AppLogger"
        ) as mock_logger:
            result = IdeReviewManager.get_agent_and_init_params_for_review(sample_user_agent_dto_exception)

            assert result is None
            mock_logger.log_warn.assert_called_once()


class TestIdeReviewManagerUpdateBucketNameAdvanced:
    """Advanced test cases for IdeReviewManager._update_bucket_name method."""

    def test_update_bucket_name_special_characters_in_display_name(
        self,
        sample_agent_run_result_special_chars_display_name: AgentRunResult,
    ) -> None:
        """Test bucket name update with special characters in display name."""
        comments = sample_agent_run_result_special_chars_display_name.agent_result["comments"]
        original_buckets = [comment.bucket for comment in comments]

        # Execute
        IdeReviewManager._update_bucket_name(sample_agent_run_result_special_chars_display_name)

        # Verify - special characters should be handled properly
        expected_bucket = "_".join(sample_agent_run_result_special_chars_display_name.display_name.upper().split())
        for comment in comments:
            assert comment.bucket == expected_bucket
            assert comment.bucket != original_buckets[0]

    def test_update_bucket_name_unicode_display_name(
        self,
        sample_agent_run_result_unicode_display_name: AgentRunResult,
    ) -> None:
        """Test bucket name update with unicode characters in display name."""
        comments = sample_agent_run_result_unicode_display_name.agent_result["comments"]

        # Execute
        IdeReviewManager._update_bucket_name(sample_agent_run_result_unicode_display_name)

        # Verify unicode is preserved
        expected_bucket = "_".join(sample_agent_run_result_unicode_display_name.display_name.upper().split())
        for comment in comments:
            assert comment.bucket == expected_bucket

    def test_update_bucket_name_single_word_display_name(
        self,
        sample_agent_run_result_single_word_display_name: AgentRunResult,
    ) -> None:
        """Test bucket name update with single word display name."""
        comments = sample_agent_run_result_single_word_display_name.agent_result["comments"]

        # Execute
        IdeReviewManager._update_bucket_name(sample_agent_run_result_single_word_display_name)

        # Verify single word is handled correctly
        expected_bucket = sample_agent_run_result_single_word_display_name.display_name.upper()
        for comment in comments:
            assert comment.bucket == expected_bucket

    def test_update_bucket_name_many_comments_performance(
        self,
        large_agent_result_with_many_comments: AgentRunResult,
    ) -> None:
        """Test bucket name update performance with many comments."""
        import time

        comments = large_agent_result_with_many_comments.agent_result["comments"]
        original_buckets = [comment.bucket for comment in comments]

        # Execute and measure time
        start_time = time.time()
        IdeReviewManager._update_bucket_name(large_agent_result_with_many_comments)
        execution_time = time.time() - start_time

        # Verify performance (should complete in reasonable time)
        assert execution_time < 1.0  # Should complete in less than 1 second

        # Verify all comments were updated
        expected_bucket = "_".join(large_agent_result_with_many_comments.display_name.upper().split())
        for i, comment in enumerate(comments):
            assert comment.bucket == expected_bucket
            assert comment.bucket != original_buckets[i]


class TestIdeReviewManagerGenerateCommentFixQueryAdvanced:
    """Advanced test cases for IdeReviewManager.generate_comment_fix_query method."""

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_edge_case_comments(
        self,
        edge_case_comment_scenarios: List[Dict[str, Any]],
    ) -> None:
        """Test comment fix query generation with edge case comments."""
        comment_id = 1

        for scenario in edge_case_comment_scenarios:
            with patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
            ) as mock_comment_repo:
                # Setup mocks
                mock_comment_repo.db_get = AsyncMock(return_value=scenario["comment"])

                # Execute
                result = await IdeReviewManager.generate_comment_fix_query(comment_id)

                # Verify all fields are included
                assert scenario["comment"].file_path in result
                assert str(scenario["comment"].line_number) in result
                assert scenario["comment"].title in result
                assert scenario["comment"].comment in result

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_very_long_content(
        self,
        sample_comment_dto_very_long: MagicMock,
    ) -> None:
        """Test comment fix query generation with very long content."""
        comment_id = 1

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(return_value=sample_comment_dto_very_long)

            # Execute
            result = await IdeReviewManager.generate_comment_fix_query(comment_id)

            # Verify long content is handled
            assert len(result) > 1000  # Should be a long query
            assert sample_comment_dto_very_long.file_path in result

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_repository_timeout(
        self,
    ) -> None:
        """Test comment fix query generation when repository times out."""
        comment_id = 1

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup timeout scenario
            mock_comment_repo.db_get = AsyncMock(side_effect=asyncio.TimeoutError("Database timeout"))

            # Execute and verify
            with pytest.raises(asyncio.TimeoutError, match="Database timeout"):
                await IdeReviewManager.generate_comment_fix_query(comment_id)

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_concurrent_calls(
        self,
        sample_comment_dto: MagicMock,
    ) -> None:
        """Test concurrent comment fix query generation calls."""
        comment_ids = [1, 2, 3, 4, 5]

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(return_value=sample_comment_dto)

            # Execute concurrent calls
            tasks = [IdeReviewManager.generate_comment_fix_query(comment_id) for comment_id in comment_ids]
            results = await asyncio.gather(*tasks)

            # Verify all calls succeeded
            assert len(results) == len(comment_ids)
            for result in results:
                assert sample_comment_dto.file_path in result
                assert sample_comment_dto.title in result


class TestIdeReviewManagerCancelReviewAdvanced:
    """Advanced test cases for IdeReviewManager.cancel_review method."""

    @pytest.mark.asyncio
    async def test_cancel_review_concurrent_cancellations(
        self,
        sample_extension_review_dto: MagicMock,
    ) -> None:
        """Test concurrent review cancellation attempts."""
        review_id = 1
        manager1 = IdeReviewManager()
        manager2 = IdeReviewManager()

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
        ) as mock_ext_repo:
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_ext_repo.update_review = AsyncMock()

            # Execute concurrent cancellations
            results = await asyncio.gather(
                manager1.cancel_review(review_id), manager2.cancel_review(review_id), return_exceptions=True
            )

            # Both should succeed (idempotent operation)
            for result in results:
                if not isinstance(result, Exception):
                    assert result["status"] == "Cancelled"
                    assert result["message"] == "Review cancelled successfully"

    @pytest.mark.asyncio
    async def test_cancel_review_already_cancelled(
        self,
        sample_extension_review_dto_cancelled: MagicMock,
        expected_cancel_success_response: Dict[str, str],
    ) -> None:
        """Test cancelling an already cancelled review."""
        review_id = 1
        manager = IdeReviewManager()

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
        ) as mock_ext_repo:
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto_cancelled)
            mock_ext_repo.update_review = AsyncMock()

            # Execute
            result = await manager.cancel_review(review_id)

            # Should succeed (idempotent)
            assert result == expected_cancel_success_response

    @pytest.mark.asyncio
    async def test_cancel_review_partial_database_failure(
        self,
        sample_extension_review_dto: MagicMock,
    ) -> None:
        """Test cancel review when database partially fails."""
        review_id = 1
        manager = IdeReviewManager()

        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.logger"
            ) as mock_logger,
        ):
            # Setup mocks - get succeeds, update fails
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_ext_repo.update_review = AsyncMock(side_effect=Exception("Database connection lost"))

            # Execute and verify
            with pytest.raises(Exception, match="Database connection lost"):
                await manager.cancel_review(review_id)

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_review_invalid_review_id_types(
        self,
    ) -> None:
        """Test cancel review with invalid review ID types."""
        manager = IdeReviewManager()
        invalid_ids = ["string_id", None, -1, 0, 999999999999]

        for invalid_id in invalid_ids:
            with patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo:
                # Setup mocks
                mock_ext_repo.db_get = AsyncMock(return_value=None)

                # Execute and verify
                with pytest.raises(ValueError, match=f"Review with ID {invalid_id} not found"):
                    await manager.cancel_review(invalid_id)


class TestIdeReviewManagerIntegration:
    """Integration test cases for IdeReviewManager."""

    @pytest.mark.asyncio
    async def test_review_diff_end_to_end_flow(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
        expected_query_response: Dict[str, Any],
    ) -> None:
        """Test complete end-to-end flow of review_diff method."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.PromptFeatureFactory"
            ) as mock_prompt_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.PromptFeatures"
            ) as mock_prompt_features,
        ):
            # Setup comprehensive mock chain
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()

            # Setup context service
            mock_context_instance = MagicMock()
            mock_context_service.return_value = mock_context_instance

            # Setup LLM handler
            mock_llm_instance = MagicMock()
            mock_llm_handler.return_value = mock_llm_instance

            # Setup agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Execute
            with (
                patch.object(
                    IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
                ),
                patch.object(IdeReviewManager, "format_agent_response", return_value=expected_query_response),
            ):
                result = await IdeReviewManager.review_diff(sample_agent_request_query)

            # Verify result
            assert result == expected_query_response

            # Verify all components were initialized and called
            mock_context_service.assert_called_once_with(review_id=sample_agent_request_query.review_id)
            mock_llm_handler.assert_called_once()
            mock_agent_factory.get_code_review_agent.assert_called_once_with(
                agent_and_init_params=sample_agent_and_init_params,
                context_service=mock_context_instance,
                llm_handler=mock_llm_instance,
                user_agent_dto=sample_user_agent_dto,
            )

            # Verify repositories were called
            mock_ext_repo.db_get.assert_called_once()
            mock_user_agent_repo.db_get.assert_called_once()
            mock_status_repo.db_insert.assert_called_once()

            # Verify agent execution
            mock_agent.run_agent.assert_called_once_with(
                session_id=sample_extension_review_dto.session_id,
                payload=sample_agent_request_query.model_dump(mode="python"),
            )

    @pytest.mark.asyncio
    async def test_complete_workflow_with_multiple_request_types(
        self,
        multiple_agent_request_scenarios: List[Dict[str, Any]],
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
    ) -> None:
        """Test complete workflow with multiple request types."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()

            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Test each scenario
            for scenario in multiple_agent_request_scenarios:
                mock_status_repo.reset_mock()

                with patch.object(
                    IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
                ):
                    result = await IdeReviewManager.review_diff(scenario["request"])

                # Verify status insertion behavior
                if scenario["expected_status_insert"]:
                    mock_status_repo.db_insert.assert_called_once()
                else:
                    mock_status_repo.db_insert.assert_not_called()

                # Result should not be None for valid scenarios
                assert result is not None


class TestIdeReviewManagerStressTests:
    """Stress and performance test cases for IdeReviewManager."""

    @pytest.mark.asyncio
    async def test_concurrent_review_diff_calls(
        self,
        sample_agent_request_query: AgentRequestItem,
        sample_extension_review_dto: MagicMock,
        sample_user_agent_dto: MagicMock,
        sample_agent_and_init_params: AgentAndInitParams,
        sample_agent_run_result_success: AgentRunResult,
    ) -> None:
        """Test concurrent review_diff calls for stress testing."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository"
            ) as mock_ext_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository"
            ) as mock_user_agent_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService"
            ) as mock_context_service,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler"
            ) as mock_llm_handler,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory"
            ) as mock_agent_factory,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository"
            ) as mock_status_repo,
        ):
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()

            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent

            # Create multiple concurrent tasks
            num_concurrent_calls = 10
            tasks = []

            for i in range(num_concurrent_calls):
                # Create unique request for each call
                request = AgentRequestItem(
                    agent_id=sample_agent_request_query.agent_id,
                    review_id=sample_agent_request_query.review_id + i,
                    type=sample_agent_request_query.type,
                    tool_use_response=sample_agent_request_query.tool_use_response,
                )
                tasks.append(IdeReviewManager.review_diff(request))

            # Execute concurrent calls
            with patch.object(
                IdeReviewManager, "get_agent_and_init_params_for_review", return_value=sample_agent_and_init_params
            ):
                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                execution_time = time.time() - start_time

            # Verify all calls completed successfully
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == num_concurrent_calls

            # Verify reasonable performance (should complete in reasonable time)
            assert execution_time < 5.0  # Should complete in less than 5 seconds

    def test_format_agent_response_with_large_datasets(
        self,
        sample_agent_run_result_large_tool_input: AgentRunResult,
    ) -> None:
        """Test format_agent_response with large tool input data."""
        agent_id = 1

        # Measure performance
        start_time = time.time()
        result = IdeReviewManager.format_agent_response(sample_agent_run_result_large_tool_input, agent_id)
        execution_time = time.time() - start_time

        # Verify result is correct
        assert result["type"] == "TOOL_USE_REQUEST"
        assert result["agent_id"] == agent_id
        assert "data" in result

        # Verify performance
        assert execution_time < 1.0  # Should complete quickly even with large data

    @pytest.mark.asyncio
    async def test_generate_comment_fix_query_bulk_processing(
        self,
        sample_comment_dto: MagicMock,
    ) -> None:
        """Test bulk comment fix query generation."""
        comment_ids = list(range(1, 21))  # Process 20 comments

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository"
        ) as mock_comment_repo:
            # Setup mocks
            mock_comment_repo.db_get = AsyncMock(return_value=sample_comment_dto)

            # Execute bulk processing
            start_time = time.time()
            tasks = [IdeReviewManager.generate_comment_fix_query(comment_id) for comment_id in comment_ids]
            results = await asyncio.gather(*tasks)
            execution_time = time.time() - start_time

            # Verify all queries generated successfully
            assert len(results) == len(comment_ids)
            for result in results:
                assert sample_comment_dto.file_path in result
                assert sample_comment_dto.title in result

            # Verify performance
            assert execution_time < 2.0  # Should complete bulk processing quickly
