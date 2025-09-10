import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List, Tuple

from app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine import (
    CommentBlendingEngine,
)
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    CommentBuckets,
    ParsedCommentData,
    ParsedAggregatedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine_fixtures import (
    CommentBlendingEngineFixtures,
)


class TestCommentBlendingEngine:
    """Test cases for CommentBlendingEngine class."""

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    def test_init(self, mock_get_context_value: Mock) -> None:
        """Test CommentBlendingEngine initialization."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        session_id = 123
        
        # Act
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=session_id
        )
        
        # Assert
        assert engine.llm_comments == llm_comments
        assert engine.context_service == mock_context_service
        assert engine.llm_handler == mock_llm_handler
        assert engine.session_id == session_id
        assert engine.MAX_RETRIES == 2
        assert isinstance(engine.filtered_comments, list)
        assert isinstance(engine.invalid_comments, list)

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    def test_get_confidence_score_limit_success(self, mock_get_context_value: Mock) -> None:
        """Test get_confidence_score_limit returns correct mapping."""
        # Arrange
        mock_setting = CommentBlendingEngineFixtures.get_mock_setting()
        mock_get_context_value.return_value = mock_setting
        
        # Act
        result = CommentBlendingEngine.get_confidence_score_limit()
        
        # Assert
        assert isinstance(result, dict)
        assert "security_agent" in result
        assert "error_agent" in result
        assert result["security_agent"]["confidence_score_limit"] == 0.7
        assert result["error_agent"]["confidence_score_limit"] == 0.8

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    def test_get_confidence_score_limit_none_setting(self, mock_get_context_value: Mock) -> None:
        """Test get_confidence_score_limit raises error when setting is None."""
        # Arrange
        mock_get_context_value.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Setting is None"):
            CommentBlendingEngine.get_confidence_score_limit()

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.SettingService')
    def test_apply_agent_confidence_score_limit(self, mock_setting_service: Mock, mock_get_context_value: Mock) -> None:
        """Test apply_agent_confidence_score_limit filters comments correctly."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        mock_setting_service.helper.agents_settings.return_value = CommentBlendingEngineFixtures.get_agent_settings()
        
        llm_comments = CommentBlendingEngineFixtures.get_llm_comments_with_various_confidence()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        # Act
        engine.apply_agent_confidence_score_limit()
        
        # Assert
        assert len(engine.filtered_comments) > 0
        # Should only include comments with confidence >= threshold
        for comment in engine.filtered_comments:
            assert comment.confidence_score >= 0.7  # Minimum threshold from mock

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    async def test_blend_comments_success(self, mock_get_context_value: Mock) -> None:
        """Test blend_comments executes successfully."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        # Mock methods
        engine.apply_agent_confidence_score_limit = Mock()
        engine.validate_comments = AsyncMock()
        engine.process_all_comments = AsyncMock()
        
        # Act
        result = await engine.blend_comments()
        
        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        filtered_comments, agent_results = result
        assert isinstance(filtered_comments, list)
        assert isinstance(agent_results, dict)
        
        engine.apply_agent_confidence_score_limit.assert_called_once()
        engine.validate_comments.assert_called_once()
        engine.process_all_comments.assert_called_once()

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    def test_extract_validated_comments(self, mock_get_context_value: Mock) -> None:
        """Test extract_validated_comments processes validation results correctly."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        # Setup filtered comments
        engine.filtered_comments = CommentBlendingEngineFixtures.get_parsed_comments()
        
        response_content = CommentBlendingEngineFixtures.get_validation_response()
        
        # Act
        result = engine.extract_validated_comments(response_content)
        
        # Assert
        assert isinstance(result, list)
        assert len(engine.invalid_comments) > 0  # Some comments should be marked invalid
        assert len(result) > 0  # Some comments should be valid

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.AgentFactory')
    async def test_validate_comments_success(self, mock_agent_factory: Mock, mock_get_context_value: Mock) -> None:
        """Test validate_comments executes successfully."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        mock_agent = Mock()
        mock_agent_result = CommentBlendingEngineFixtures.get_mock_agent_result()
        mock_agent.run_agent = AsyncMock(return_value=mock_agent_result)
        mock_agent_factory.get_review_finalization_agents.return_value = [mock_agent]
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        engine.filtered_comments = CommentBlendingEngineFixtures.get_parsed_comments()
        engine.extract_validated_comments = Mock(return_value=[])
        
        # Act
        await engine.validate_comments()
        
        # Assert
        mock_agent_factory.get_review_finalization_agents.assert_called_once()
        mock_agent.run_agent.assert_called_once_with(session_id=123)

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    async def test_validate_comments_empty_list(self, mock_get_context_value: Mock) -> None:
        """Test validate_comments returns early when no comments to validate."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        engine.filtered_comments = []
        
        # Act
        await engine.validate_comments()
        
        # Assert - Should return early without processing

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.extract_line_number_from_llm_response')
    def test_aggregate_comments_by_line(self, mock_extract_line: Mock, mock_get_context_value: Mock) -> None:
        """Test aggregate_comments_by_line groups comments correctly."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        mock_extract_line.side_effect = lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 1
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        engine.filtered_comments = CommentBlendingEngineFixtures.get_parsed_comments_multiple_lines()
        
        # Act
        result = engine.aggregate_comments_by_line()
        
        # Assert
        assert isinstance(result, dict)
        for file_path, lines in result.items():
            assert isinstance(lines, dict)
            for line_number, data in lines.items():
                assert isinstance(data, ParsedAggregatedCommentData)
                assert data.file_path == file_path
                assert data.line_number == line_number

    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    def test_split_single_and_multi_comments(self, mock_get_context_value: Mock) -> None:
        """Test split_single_and_multi_comments separates comments correctly."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        # Mock aggregate_comments_by_line
        engine.aggregate_comments_by_line = Mock(return_value=CommentBlendingEngineFixtures.get_aggregated_comments())
        
        # Act
        single_comments, multi_comments = engine.split_single_and_multi_comments()
        
        # Assert
        assert isinstance(single_comments, list)
        assert isinstance(multi_comments, list)
        for comment in single_comments:
            assert isinstance(comment, ParsedCommentData)
        for comment in multi_comments:
            assert isinstance(comment, ParsedAggregatedCommentData)

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    async def test_process_all_comments_no_comments(self, mock_get_context_value: Mock) -> None:
        """Test process_all_comments returns None when no comments."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        engine.filtered_comments = []
        
        # Act
        result = await engine.process_all_comments()
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.get_context_value')
    @patch('app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine.AgentFactory')
    async def test_validate_comments_json_decode_error_retry(self, mock_agent_factory: Mock, mock_get_context_value: Mock) -> None:
        """Test validate_comments retries on JSON decode error."""
        # Arrange
        mock_get_context_value.return_value = CommentBlendingEngineFixtures.get_mock_setting()
        
        mock_agent = Mock()
        mock_agent.run_agent = AsyncMock(side_effect=[
            json.JSONDecodeError("Invalid JSON", "", 0),
            CommentBlendingEngineFixtures.get_mock_agent_result()
        ])
        mock_agent_factory.get_review_finalization_agents.return_value = [mock_agent]
        
        llm_comments = CommentBlendingEngineFixtures.get_sample_llm_comments()
        mock_context_service = Mock(spec=ContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        
        engine = CommentBlendingEngine(
            llm_comments=llm_comments,
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            session_id=123
        )
        
        engine.filtered_comments = CommentBlendingEngineFixtures.get_parsed_comments()
        engine.extract_validated_comments = Mock(return_value=[])
        
        # Act
        await engine.validate_comments()
        
        # Assert
        assert mock_agent.run_agent.call_count == 2  # Should retry once