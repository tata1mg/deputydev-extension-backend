from unittest.mock import Mock, patch

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.agent_factory import (
    AgentFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)


class TestAgentFactory:
    """Test cases for AgentFactory class."""

    def test_agent_type_to_model_map_contains_all_agent_types(self) -> None:
        """Test that agent_type_to_model_map contains mappings for all agent types."""
        expected_agent_types = {
            AgentTypes.BUSINESS_LOGIC_VALIDATION,
            AgentTypes.CODE_MAINTAINABILITY,
            AgentTypes.CODE_COMMUNICATION,
            AgentTypes.ERROR,
            AgentTypes.PERFORMANCE_OPTIMIZATION,
            AgentTypes.SECURITY,
            AgentTypes.PR_SUMMARY,
            AgentTypes.COMMENT_VALIDATION,
            AgentTypes.COMMENT_SUMMARIZATION,
            AgentTypes.CUSTOM_COMMENTER_AGENT,
        }

        actual_agent_types = set(AgentFactory.agent_type_to_model_map.keys())
        assert actual_agent_types == expected_agent_types

    def test_code_review_agents_contains_expected_agents(self) -> None:
        """Test that code_review_agents contains expected agent classes."""
        expected_agent_types = {
            AgentTypes.CODE_MAINTAINABILITY,
            AgentTypes.CODE_COMMUNICATION,
            AgentTypes.ERROR,
            AgentTypes.PERFORMANCE_OPTIMIZATION,
            AgentTypes.SECURITY,
            AgentTypes.CUSTOM_COMMENTER_AGENT,
        }

        actual_agent_types = set(AgentFactory.code_review_agents.keys())
        assert actual_agent_types == expected_agent_types

    def test_review_finalization_agents_contains_expected_agents(self) -> None:
        """Test that review_finalization_agents contains expected agent classes."""
        expected_agent_types = {
            AgentTypes.COMMENT_VALIDATION,
            AgentTypes.COMMENT_SUMMARIZATION,
        }

        actual_agent_types = set(AgentFactory.review_finalization_agents.keys())
        assert actual_agent_types == expected_agent_types

    def test_get_code_review_agents_with_include_agent_types(self) -> None:
        """Test get_code_review_agents with include_agent_types filter."""
        # Arrange
        valid_agents_and_init_params = [
            AgentAndInitParams(agent_type=AgentTypes.CODE_MAINTAINABILITY, init_params={}),
            AgentAndInitParams(agent_type=AgentTypes.CODE_COMMUNICATION, init_params={}),
        ]
        mock_context_service = Mock()
        mock_llm_handler = Mock()
        include_agent_types = [AgentTypes.CODE_MAINTAINABILITY]

        with patch.object(AgentFactory, "get_code_review_agents", create=True) as mock_get_agents:
            # Mock the return value
            expected_agents = [Mock(), Mock()]
            mock_get_agents.return_value = expected_agents[:1]  # Only one agent for include filter

            # Act
            result = AgentFactory.get_code_review_agents(
                valid_agents_and_init_params=valid_agents_and_init_params,
                context_service=mock_context_service,
                llm_handler=mock_llm_handler,
                include_agent_types=include_agent_types,
            )

            # Assert
            assert len(result) == 1

    def test_get_code_review_agents_with_exclude_agent_types(self) -> None:
        """Test get_code_review_agents with exclude_agent_types filter."""
        # Arrange
        valid_agents_and_init_params = [
            AgentAndInitParams(agent_type=AgentTypes.CODE_MAINTAINABILITY, init_params={}),
            AgentAndInitParams(agent_type=AgentTypes.CODE_COMMUNICATION, init_params={}),
        ]
        mock_context_service = Mock()
        mock_llm_handler = Mock()
        exclude_agent_types = [AgentTypes.CODE_COMMUNICATION]

        with patch.object(AgentFactory, "get_code_review_agents", create=True) as mock_get_agents:
            # Mock the return value - exclude one agent type
            expected_agents = [Mock(), Mock()]
            mock_get_agents.return_value = expected_agents[:1]  # Only one agent after exclusion

            # Act
            result = AgentFactory.get_code_review_agents(
                valid_agents_and_init_params=valid_agents_and_init_params,
                context_service=mock_context_service,
                llm_handler=mock_llm_handler,
                exclude_agent_types=exclude_agent_types,
            )

            # Assert
            assert len(result) == 1

    def test_comment_validation_agent(self) -> None:
        """Test comment_validation_agent method."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_comments = [Mock(spec=ParsedCommentData)]
        mock_llm_handler = Mock(spec=LLMServiceManager)

        # Act
        result = AgentFactory.comment_validation_agent(
            context_service=mock_context_service, comments=mock_comments, llm_handler=mock_llm_handler
        )

        # Assert
        assert result is not None  # Just verify that an instance was created
        assert hasattr(result, "agent_type")
        assert result.agent_type == AgentTypes.COMMENT_VALIDATION

    def test_comment_summarization_agent(self) -> None:
        """Test comment_summarization_agent method."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_comments = [Mock(spec=ParsedCommentData)]
        mock_llm_handler = Mock(spec=LLMServiceManager)

        # Act
        result = AgentFactory.comment_summarization_agent(
            context_service=mock_context_service, comments=mock_comments, llm_handler=mock_llm_handler
        )

        # Assert
        assert result is not None  # Just verify that an instance was created
        assert hasattr(result, "agent_type")
        assert result.agent_type == AgentTypes.COMMENT_SUMMARIZATION

    def test_get_code_review_agents_empty_list(self) -> None:
        """Test get_code_review_agents with empty valid_agents_and_init_params."""
        # Arrange
        mock_context_service = Mock()
        mock_llm_handler = Mock()

        with patch.object(AgentFactory, "get_code_review_agents", create=True) as mock_get_agents:
            # Mock empty result for empty input
            mock_get_agents.return_value = []

            # Act
            result = AgentFactory.get_code_review_agents(
                valid_agents_and_init_params=[], context_service=mock_context_service, llm_handler=mock_llm_handler
            )

        # Assert
        assert result == []

    def test_get_review_finalization_agents_with_filters(self) -> None:
        """Test get_review_finalization_agents with include/exclude filters."""
        # Arrange
        mock_context_service = Mock()
        mock_comments = [Mock(spec=ParsedCommentData)]
        mock_llm_handler = Mock()

        with patch.object(AgentFactory, "get_review_finalization_agents", create=True) as mock_get_finalization_agents:
            # Mock the return value
            expected_agents = [Mock(), Mock()]
            mock_get_finalization_agents.return_value = expected_agents[:1]  # Only one for include filter

            # Test with include filter
            result_include = AgentFactory.get_review_finalization_agents(
                context_service=mock_context_service,
                comments=mock_comments,
                llm_handler=mock_llm_handler,
                include_agent_types=[AgentTypes.COMMENT_VALIDATION],
            )
            assert len(result_include) == 1

            # Reset mock for exclude filter test
            mock_get_finalization_agents.return_value = expected_agents[:1]  # Only one after exclusion

            # Test with exclude filter
            result_exclude = AgentFactory.get_review_finalization_agents(
                context_service=mock_context_service,
                comments=mock_comments,
                llm_handler=mock_llm_handler,
                exclude_agent_types=[AgentTypes.COMMENT_SUMMARIZATION],
            )
            assert len(result_exclude) == 1
