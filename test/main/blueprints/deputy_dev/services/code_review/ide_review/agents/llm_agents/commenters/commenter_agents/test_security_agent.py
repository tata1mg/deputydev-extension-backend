import pytest
from unittest.mock import Mock
from typing import Dict

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.security_agent import (
    SecurityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.models.dto.message_thread_dto import LLModels
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.security_agent_fixtures import (
    SecurityAgentFixtures,
)


class TestSecurityAgent:
    """Test cases for SecurityAgent class."""

    def test_class_attributes(self) -> None:
        """Test SecurityAgent class attributes are correctly set."""
        # Assert
        assert SecurityAgent.is_dual_pass is False
        assert SecurityAgent.prompt_features == [PromptFeatures.SECURITY_COMMENTS_GENERATION]
        assert SecurityAgent.agent_type == AgentTypes.SECURITY

    def test_init_inherits_from_base_commenter_agent(self) -> None:
        """Test SecurityAgent inherits from BaseCommenterAgent."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        # Act
        agent = SecurityAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=model,
            user_agent_dto=mock_user_agent_dto
        )
        
        # Assert
        assert agent.context_service == mock_context_service
        assert agent.llm_handler == mock_llm_handler
        assert agent.model == model

    def test_get_agent_specific_tokens_data_returns_empty_dict(self) -> None:
        """Test get_agent_specific_tokens_data returns empty dict."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        agent = SecurityAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=model,
            user_agent_dto=mock_user_agent_dto
        )
        
        # Act
        result = agent.get_agent_specific_tokens_data()
        
        # Assert
        assert isinstance(result, dict)
        assert result == {}

    def test_agent_type_is_security(self) -> None:
        """Test SecurityAgent agent_type is SECURITY."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        agent = SecurityAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=model,
            user_agent_dto=mock_user_agent_dto
        )
        
        # Act & Assert
        assert agent.agent_type == AgentTypes.SECURITY

    def test_prompt_features_contains_security_generation(self) -> None:
        """Test SecurityAgent prompt_features contains SECURITY_COMMENTS_GENERATION."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        agent = SecurityAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=model,
            user_agent_dto=mock_user_agent_dto
        )
        
        # Act & Assert
        assert PromptFeatures.SECURITY_COMMENTS_GENERATION in agent.prompt_features
        assert len(agent.prompt_features) == 1

    def test_is_dual_pass_is_false(self) -> None:
        """Test SecurityAgent is_dual_pass is False."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        agent = SecurityAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=model,
            user_agent_dto=mock_user_agent_dto
        )
        
        # Act & Assert
        assert agent.is_dual_pass is False

    def test_initialization_with_different_models(self) -> None:
        """Test SecurityAgent initialization with different models."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        models = SecurityAgentFixtures.get_various_llm_models()
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        for model in models:
            # Act
            agent = SecurityAgent(
                context_service=mock_context_service,
                llm_handler=mock_llm_handler,
                model=model,
                user_agent_dto=mock_user_agent_dto
            )
            
            # Assert
            assert agent.model == model
            assert agent.agent_type == AgentTypes.SECURITY

    def test_initialization_with_additional_kwargs(self) -> None:
        """Test SecurityAgent initialization with additional keyword arguments."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        # Act - Test that base constructor doesn't accept additional kwargs
        with pytest.raises(TypeError):
            agent = SecurityAgent(
                context_service=mock_context_service,
                llm_handler=mock_llm_handler,
                model=model,
                user_agent_dto=mock_user_agent_dto,
                custom_param="test_value"  # This should fail
            )

    def test_get_agent_specific_tokens_data_return_type(self) -> None:
        """Test get_agent_specific_tokens_data returns correct type."""
        # Arrange
        mock_context_service = Mock(spec=IdeReviewContextService)
        mock_llm_handler = Mock(spec=LLMHandler)
        model = LLModels.CLAUDE_3_POINT_7_SONNET
        mock_user_agent_dto = Mock()
        mock_user_agent_dto.id = 1
        mock_user_agent_dto.agent_name = "test_agent"
        mock_user_agent_dto.display_name = "Test Agent"
        mock_user_agent_dto.objective = "Test objective"
        mock_user_agent_dto.custom_prompt = "Test prompt"
        mock_user_agent_dto.confidence_score = 0.8
        
        agent = SecurityAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=model,
            user_agent_dto=mock_user_agent_dto
        )
        
        # Act
        result = agent.get_agent_specific_tokens_data()
        
        # Assert
        assert isinstance(result, dict)
        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, int)