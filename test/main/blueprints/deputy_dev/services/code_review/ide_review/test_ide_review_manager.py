"""
Unit tests for IdeReviewManager.

This module provides comprehensive unit tests for the IdeReviewManager class,
covering all methods including review_diff, format_agent_response, 
get_agent_and_init_params_for_review, generate_comment_fix_query, 
and cancel_review with various scenarios including edge cases and error handling.
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    RequestType,
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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository') as mock_user_agent_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService') as mock_context_service, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler') as mock_llm_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory') as mock_agent_factory, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository') as mock_status_repo:
            
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()
            
            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_success)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent
            
            # Execute
            with patch.object(IdeReviewManager, 'get_agent_and_init_params_for_review', return_value=sample_agent_and_init_params):
                result = await IdeReviewManager.review_diff(sample_agent_request_query)
            
            # Verify
            assert result == expected_query_response
            mock_ext_repo.db_get.assert_called_once_with(filters={"id": sample_agent_request_query.review_id}, fetch_one=True)
            mock_user_agent_repo.db_get.assert_called_once_with(filters={"id": sample_agent_request_query.agent_id}, fetch_one=True)
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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository') as mock_user_agent_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService') as mock_context_service, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler') as mock_llm_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory') as mock_agent_factory, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository') as mock_status_repo:
            
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            
            # Mock agent
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(return_value=sample_agent_run_result_tool_use)
            mock_agent_factory.get_code_review_agent.return_value = mock_agent
            
            # Execute
            with patch.object(IdeReviewManager, 'get_agent_and_init_params_for_review', return_value=sample_agent_and_init_params):
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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository') as mock_user_agent_repo:
            
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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository') as mock_user_agent_repo:
            
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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository') as mock_user_agent_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService') as mock_context_service, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler') as mock_llm_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory') as mock_agent_factory, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository') as mock_status_repo:
            
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_user_agent_repo.db_get = AsyncMock(return_value=sample_user_agent_dto)
            mock_status_repo.db_insert = AsyncMock()
            
            # Mock agent to fail
            mock_agent = MagicMock()
            mock_agent.run_agent = AsyncMock(side_effect=Exception("Agent execution failed"))
            mock_agent_factory.get_code_review_agent.return_value = mock_agent
            
            # Execute and verify
            with patch.object(IdeReviewManager, 'get_agent_and_init_params_for_review', return_value=sample_agent_and_init_params):
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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AppLogger') as mock_logger:
            result = IdeReviewManager.get_agent_and_init_params_for_review(sample_user_agent_dto_invalid_agent)
            
            assert result is None
            mock_logger.log_warn.assert_called_once_with(f"Invalid agent name: {sample_user_agent_dto_invalid_agent.agent_name}")

    def test_get_agent_and_init_params_none_agent_name(
        self,
        sample_user_agent_dto_none_agent: MagicMock,
    ) -> None:
        """Test handling of None agent name."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AppLogger') as mock_logger:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository') as mock_comment_repo:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository') as mock_comment_repo:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository') as mock_comment_repo:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeCommentRepository') as mock_comment_repo:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo:
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.logger') as mock_logger:
            
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
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.logger') as mock_logger:
            
            # Setup mocks
            mock_ext_repo.db_get = AsyncMock(return_value=sample_extension_review_dto)
            mock_ext_repo.update_review = AsyncMock(side_effect=Exception("Database update error"))
            
            # Execute and verify
            with pytest.raises(Exception, match="Database update error"):
                await manager.cancel_review(review_id)
            
            mock_logger.error.assert_called_once()


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
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ExtensionReviewsRepository') as mock_ext_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.UserAgentRepository') as mock_user_agent_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.IdeReviewContextService') as mock_context_service, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.LLMHandler') as mock_llm_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.AgentFactory') as mock_agent_factory, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.ReviewAgentStatusRepository') as mock_status_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.PromptFeatureFactory') as mock_prompt_factory, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager.PromptFeatures') as mock_prompt_features:
            
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
            with patch.object(IdeReviewManager, 'get_agent_and_init_params_for_review', return_value=sample_agent_and_init_params), \
                 patch.object(IdeReviewManager, 'format_agent_response', return_value=expected_query_response):
                
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
                payload=sample_agent_request_query.model_dump(mode="python")
            )