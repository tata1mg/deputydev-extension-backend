"""
Unit tests for BaseCodeReviewAgent.

This module contains comprehensive unit tests for the BaseCodeReviewAgent class,
testing all methods including initialization, abstract methods, token handling,
agent execution logic, and edge cases.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    LLMCallResponseTypes,
    NonStreamingParsedLLMCallResponse,
    UserAndSystemMessages,
)

from app.backend_common.models.dto.message_thread_dto import LLModels, LLMUsage
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent_fixtures import *


# Concrete implementation of BaseCodeReviewAgent for testing
class TestAgent(BaseCodeReviewAgent):
    """Test implementation of BaseCodeReviewAgent."""

    agent_type = AgentTypes.SECURITY
    agent_name = "test_security_agent"
    is_dual_pass = False
    prompt_features = [PromptFeatures.SECURITY_COMMENTS_GENERATION]

    async def required_prompt_variables(self) -> Dict[str, Optional[str]]:
        """Implementation of abstract method for testing."""
        return {"code_content": "def test(): pass", "file_path": "/test/file.py"}

    def get_display_name(self) -> str:
        """Implementation of abstract method for testing."""
        return "Test Security Agent"


class TestDualPassAgent(BaseCodeReviewAgent):
    """Test implementation of BaseCodeReviewAgent with dual pass."""

    agent_type = AgentTypes.CODE_COMMUNICATION
    agent_name = "test_communication_agent"
    is_dual_pass = True
    prompt_features = [
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_1,
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_2,
    ]

    async def required_prompt_variables(self) -> Dict[str, Optional[str]]:
        """Implementation of abstract method for testing."""
        return {"code_content": "def test(): return True", "context": "Test context"}

    def get_display_name(self) -> str:
        """Implementation of abstract method for testing."""
        return "Test Communication Agent"


class TestBaseCodeReviewAgentInitialization:
    """Test BaseCodeReviewAgent initialization."""

    def test_init_single_pass_agent(self, mock_context_service: MagicMock, mock_llm_handler: MagicMock) -> None:
        """Test initialization of single pass agent."""
        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        assert agent.context_service == mock_context_service
        assert agent.llm_handler == mock_llm_handler
        assert agent.model == LLModels.GPT_4O
        assert agent.agent_name == TestAgent.agent_type.value
        assert agent.tiktoken is not None
        assert not agent.is_dual_pass
        assert len(agent.prompt_features) == 1

    def test_init_dual_pass_agent(self, mock_context_service: MagicMock, mock_llm_handler: MagicMock) -> None:
        """Test initialization of dual pass agent."""
        agent = TestDualPassAgent(
            context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_40_MINI
        )

        assert agent.context_service == mock_context_service
        assert agent.llm_handler == mock_llm_handler
        assert agent.model == LLModels.GPT_40_MINI
        assert agent.agent_name == TestDualPassAgent.agent_type.value
        assert agent.is_dual_pass
        assert len(agent.prompt_features) == 2

    def test_init_with_all_models(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, all_llm_models: List[LLModels]
    ) -> None:
        """Test initialization with all available LLM models."""
        for model in all_llm_models:
            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=model)
            assert agent.model == model


class TestBaseCodeReviewAgentShouldExecute:
    """Test BaseCodeReviewAgent should_execute method."""

    @pytest.mark.asyncio
    async def test_should_execute_default_returns_true(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock
    ) -> None:
        """Test that should_execute returns True by default."""
        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = await agent.should_execute()
        assert result is True

    @pytest.mark.asyncio
    async def test_should_execute_can_be_overridden(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock
    ) -> None:
        """Test that should_execute can be overridden in subclasses."""

        class CustomAgent(TestAgent):
            async def should_execute(self) -> bool:
                return False

        agent = CustomAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = await agent.should_execute()
        assert result is False


class TestBaseCodeReviewAgentTokenHandling:
    """Test BaseCodeReviewAgent token handling methods."""

    def test_get_agent_specific_tokens_data_default(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock
    ) -> None:
        """Test get_agent_specific_tokens_data returns empty dict by default."""
        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = agent.get_agent_specific_tokens_data()
        assert result == {}

    def test_get_agent_specific_tokens_data_can_be_overridden(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock
    ) -> None:
        """Test get_agent_specific_tokens_data can be overridden."""

        class CustomAgent(TestAgent):
            def get_agent_specific_tokens_data(self) -> Dict[str, Any]:
                return {"custom_token": 100}

        agent = CustomAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = agent.get_agent_specific_tokens_data()
        assert result == {"custom_token": 100}

    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.TikToken")
    def test_get_tokens_data(
        self,
        mock_tiktoken_class: MagicMock,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_and_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test get_tokens_data calculates tokens correctly."""
        mock_tiktoken_instance = MagicMock()
        mock_tiktoken_instance.count.side_effect = [100, 50]  # system, user
        mock_tiktoken_class.return_value = mock_tiktoken_instance

        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = agent.get_tokens_data(sample_user_and_system_messages)

        assert result["system_prompt"] == 100
        assert result["user_prompt"] == 50
        assert mock_tiktoken_instance.count.call_count == 2

    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.TikToken")
    def test_get_tokens_data_with_empty_system_message(
        self, mock_tiktoken_class: MagicMock, mock_context_service: MagicMock, mock_llm_handler: MagicMock
    ) -> None:
        """Test get_tokens_data handles empty system message."""
        mock_tiktoken_instance = MagicMock()
        mock_tiktoken_instance.count.side_effect = [0, 50]  # empty system, user
        mock_tiktoken_class.return_value = mock_tiktoken_instance

        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        messages = UserAndSystemMessages(system_message=None, user_message="Test user message")

        result = agent.get_tokens_data(messages)

        assert result["system_prompt"] == 0
        assert result["user_prompt"] == 50

    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG")
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.TikToken")
    def test_has_exceeded_token_limit_false(
        self,
        mock_tiktoken_class: MagicMock,
        mock_config: MagicMock,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_and_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test has_exceeded_token_limit returns False when within limits."""
        mock_tiktoken_instance = MagicMock()
        mock_tiktoken_instance.count.return_value = 1000
        mock_tiktoken_class.return_value = mock_tiktoken_instance

        mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 2000}}}

        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = agent.has_exceeded_token_limit(sample_user_and_system_messages)
        assert result is False

    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG")
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.TikToken")
    @patch("app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.AppLogger")
    def test_has_exceeded_token_limit_true(
        self,
        mock_logger: MagicMock,
        mock_tiktoken_class: MagicMock,
        mock_config: MagicMock,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_and_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test has_exceeded_token_limit returns True when exceeding limits."""
        mock_tiktoken_instance = MagicMock()
        mock_tiktoken_instance.count.return_value = 3000
        mock_tiktoken_class.return_value = mock_tiktoken_instance

        mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 2000}}}

        agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

        result = agent.has_exceeded_token_limit(sample_user_and_system_messages)
        assert result is True
        mock_logger.log_info.assert_called_once()


class TestBaseCodeReviewAgentRunAgent:
    """Test BaseCodeReviewAgent run_agent method."""

    @pytest.mark.asyncio
    async def test_run_agent_single_pass_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        valid_session_id: int,
    ) -> None:
        """Test successful single pass agent run."""
        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

            result = await agent.run_agent(valid_session_id)

            assert isinstance(result, AgentRunResult)
            assert result.agent_result == "Test response content"
            assert result.prompt_tokens_exceeded is False
            assert result.agent_name == "security"
            assert result.agent_type == AgentTypes.SECURITY
            assert result.model == LLModels.GPT_4O
            assert result.display_name == "Test Security Agent"
            assert "securityPASS_1" in result.tokens_data

    @pytest.mark.asyncio
    async def test_run_agent_dual_pass_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        sample_llm_response_dual_pass: List[NonStreamingParsedLLMCallResponse],
        valid_session_id: int,
    ) -> None:
        """Test successful dual pass agent run."""
        # Setup mocks for dual pass
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.side_effect = sample_llm_response_dual_pass

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestDualPassAgent(
                context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O
            )

            result = await agent.run_agent(valid_session_id)

            assert isinstance(result, AgentRunResult)
            assert result.agent_result == "Second pass response"
            assert result.prompt_tokens_exceeded is False
            assert result.agent_name == "code_communication"
            assert result.agent_type == AgentTypes.CODE_COMMUNICATION
            assert "code_communicationPASS_1" in result.tokens_data
            assert "code_communicationPASS_2" in result.tokens_data
            assert mock_llm_handler.start_llm_query.call_count == 2

    @pytest.mark.asyncio
    async def test_run_agent_token_limit_exceeded(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        valid_session_id: int,
    ) -> None:
        """Test agent run when token limit is exceeded."""
        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler

        # Mock large token count
        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {
                "LLM_MODELS": {
                    "GPT_4O": {"INPUT_TOKENS_LIMIT": 100}  # Very low limit
                }
            }

            with patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.TikToken"
            ) as mock_tiktoken_class:
                mock_tiktoken_instance = MagicMock()
                mock_tiktoken_instance.count.return_value = 200  # Exceeds limit
                mock_tiktoken_class.return_value = mock_tiktoken_instance

                agent = TestAgent(
                    context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O
                )

                result = await agent.run_agent(valid_session_id)

                assert isinstance(result, AgentRunResult)
                assert result.agent_result is None
                assert result.prompt_tokens_exceeded is True
                assert result.agent_name == "security"
                assert result.agent_type == AgentTypes.SECURITY
                # LLM handler should not be called when token limit exceeded
                mock_llm_handler.start_llm_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_agent_invalid_llm_response(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        invalid_llm_response: MagicMock,
        valid_session_id: int,
    ) -> None:
        """Test agent run with invalid LLM response type."""
        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = invalid_llm_response

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

            with pytest.raises(ValueError, match="LLM Response is not of type NonStreamingParsedLLMCallResponse"):
                await agent.run_agent(valid_session_id)

    @pytest.mark.asyncio
    async def test_run_agent_llm_handler_exception(
        self,
        mock_context_service: MagicMock,
        llm_handler_with_exception: MagicMock,
        mock_prompt_handler: MagicMock,
        valid_session_id: int,
    ) -> None:
        """Test agent run when LLM handler raises exception."""
        # Setup mocks
        llm_handler_with_exception.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(
                context_service=mock_context_service, llm_handler=llm_handler_with_exception, model=LLModels.GPT_4O
            )

            with pytest.raises(Exception, match="LLM query failed"):
                await agent.run_agent(valid_session_id)

    @pytest.mark.asyncio
    async def test_run_agent_multiple_content_blocks(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        sample_llm_response_multiple_content: NonStreamingParsedLLMCallResponse,
        valid_session_id: int,
    ) -> None:
        """Test agent run with multiple content blocks (uses first one)."""
        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response_multiple_content

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

            result = await agent.run_agent(valid_session_id)

            assert result.agent_result == "Content block 1"  # First content block


class TestBaseCodeReviewAgentEdgeCases:
    """Test BaseCodeReviewAgent edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_run_agent_with_zero_session_id(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        zero_session_id: int,
    ) -> None:
        """Test agent run with zero session ID."""
        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

            result = await agent.run_agent(zero_session_id)

            assert isinstance(result, AgentRunResult)
            assert result.prompt_tokens_exceeded is False
            mock_llm_handler.start_llm_query.assert_called_once_with(
                session_id=zero_session_id,
                prompt_feature=PromptFeatures.SECURITY_COMMENTS_GENERATION,
                llm_model=LLModels.GPT_4O,
                prompt_vars={"code_content": "def test(): pass", "file_path": "/test/file.py"},
            )

    @pytest.mark.asyncio
    async def test_run_agent_with_negative_session_id(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        invalid_session_id: int,
    ) -> None:
        """Test agent run with negative session ID."""
        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

            result = await agent.run_agent(invalid_session_id)

            assert isinstance(result, AgentRunResult)
            mock_llm_handler.start_llm_query.assert_called_once_with(
                session_id=invalid_session_id,
                prompt_feature=PromptFeatures.SECURITY_COMMENTS_GENERATION,
                llm_model=LLModels.GPT_4O,
                prompt_vars={"code_content": "def test(): pass", "file_path": "/test/file.py"},
            )

    def test_agent_with_all_agent_types(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, all_agent_types: List[AgentTypes]
    ) -> None:
        """Test agent initialization with all available agent types."""
        for agent_type_enum in all_agent_types:

            def create_dynamic_agent(agent_type_val: AgentTypes) -> type:
                class DynamicTestAgent(BaseCodeReviewAgent):
                    agent_type = agent_type_val
                    agent_name = f"test_{agent_type_val.value}_agent"
                    is_dual_pass = False
                    prompt_features = [PromptFeatures.SECURITY_COMMENTS_GENERATION]

                    async def required_prompt_variables(self) -> Dict[str, Optional[str]]:
                        return {"test": "value"}

                    def get_display_name(self) -> str:
                        return f"Test {agent_type_val.value.replace('_', ' ').title()} Agent"

                return DynamicTestAgent

            DynamicTestAgent = create_dynamic_agent(agent_type_enum)

            agent = DynamicTestAgent(
                context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O
            )

            assert agent.agent_type == agent_type_enum
            assert agent.agent_name == agent_type_enum.value
            expected_display_name = f"Test {agent_type_enum.value.replace('_', ' ').title()} Agent"
            assert agent.get_display_name() == expected_display_name


class TestBaseCodeReviewAgentPerformance:
    """Test BaseCodeReviewAgent performance and stress scenarios."""

    @pytest.mark.asyncio
    async def test_run_agent_with_large_prompt_variables(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        mock_prompt_handler: MagicMock,
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        valid_session_id: int,
    ) -> None:
        """Test agent run with large prompt variables."""
        large_content = "x" * 10000  # 10k characters

        class LargeContentAgent(TestAgent):
            async def required_prompt_variables(self) -> Dict[str, Optional[str]]:
                return {
                    "code_content": large_content,
                    "file_path": "/test/very/long/path/to/file.py",
                    "context": large_content,
                }

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = LargeContentAgent(
                context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O
            )

            result = await agent.run_agent(valid_session_id)

            assert isinstance(result, AgentRunResult)
            assert result.prompt_tokens_exceeded is False

            # Verify prompt variables were passed correctly
            call_args = mock_llm_handler.start_llm_query.call_args
            prompt_vars = call_args[1]["prompt_vars"]
            assert prompt_vars["code_content"] == large_content
            assert len(prompt_vars["context"]) == 10000


class TestBaseCodeReviewAgentIntegration:
    """Test BaseCodeReviewAgent integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_agent_workflow_single_pass(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, valid_session_id: int
    ) -> None:
        """Test complete agent workflow for single pass."""
        # Create realistic LLM response
        llm_response = NonStreamingParsedLLMCallResponse(
            type=LLMCallResponseTypes.NON_STREAMING,
            parsed_content=["Security review completed successfully"],
            content=[],
            usage=LLMUsage(input=150, output=75),
            prompt_vars={},
            prompt_id="test_prompt",
            model_used=LLModels.GPT_4O,
            query_id=123,
        )

        # Setup realistic prompt handler
        mock_prompt_handler = MagicMock()
        mock_prompt_handler.get_prompt.return_value = UserAndSystemMessages(
            system_message="You are a security code reviewer.", user_message="Review this code: def test(): pass"
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = llm_response

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestAgent(context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O)

            # Execute full workflow
            should_execute = await agent.should_execute()
            assert should_execute is True

            result = await agent.run_agent(valid_session_id)

            # Verify complete result
            assert isinstance(result, AgentRunResult)
            assert result.agent_result == "Security review completed successfully"
            assert result.prompt_tokens_exceeded is False
            assert result.agent_name == "security"
            assert result.agent_type == AgentTypes.SECURITY
            assert result.model == LLModels.GPT_4O
            assert result.display_name == "Test Security Agent"

            # Verify tokens data structure
            assert "securityPASS_1" in result.tokens_data
            tokens_data = result.tokens_data["securityPASS_1"]
            assert "system_prompt" in tokens_data
            assert "user_prompt" in tokens_data
            assert "input_tokens" in tokens_data
            assert "output_tokens" in tokens_data
            assert tokens_data["input_tokens"] == 150
            assert tokens_data["output_tokens"] == 75

    @pytest.mark.asyncio
    async def test_full_agent_workflow_dual_pass(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, valid_session_id: int
    ) -> None:
        """Test complete agent workflow for dual pass."""
        # Create realistic dual pass LLM responses
        first_response = NonStreamingParsedLLMCallResponse(
            type=LLMCallResponseTypes.NON_STREAMING,
            parsed_content=["First pass analysis complete"],
            content=[],
            usage=LLMUsage(input=100, output=50),
            prompt_vars={},
            prompt_id="test_prompt_1",
            model_used=LLModels.GPT_4O,
            query_id=123,
        )

        second_response = NonStreamingParsedLLMCallResponse(
            type=LLMCallResponseTypes.NON_STREAMING,
            parsed_content=["Final analysis with improvements"],
            content=[],
            usage=LLMUsage(input=120, output=60),
            prompt_vars={},
            prompt_id="test_prompt_2",
            model_used=LLModels.GPT_4O,
            query_id=124,
        )

        # Setup realistic prompt handler
        mock_prompt_handler = MagicMock()
        mock_prompt_handler.get_prompt.return_value = UserAndSystemMessages(
            system_message="You are a code communication reviewer.",
            user_message="Review this code for communication: def test(): return True",
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.side_effect = [first_response, second_response]

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent.CONFIG"
        ) as mock_config:
            mock_config.config = {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}}}

            agent = TestDualPassAgent(
                context_service=mock_context_service, llm_handler=mock_llm_handler, model=LLModels.GPT_4O
            )

            # Execute full workflow
            result = await agent.run_agent(valid_session_id)

            # Verify complete result
            assert isinstance(result, AgentRunResult)
            assert result.agent_result == "Final analysis with improvements"  # Second pass result
            assert result.prompt_tokens_exceeded is False
            assert result.agent_name == "code_communication"
            assert result.agent_type == AgentTypes.CODE_COMMUNICATION

            # Verify both passes were called
            assert mock_llm_handler.start_llm_query.call_count == 2

            # Verify tokens data for both passes
            assert "code_communicationPASS_1" in result.tokens_data
            assert "code_communicationPASS_2" in result.tokens_data

            pass1_tokens = result.tokens_data["code_communicationPASS_1"]
            pass2_tokens = result.tokens_data["code_communicationPASS_2"]

            assert pass1_tokens["input_tokens"] == 100
            assert pass1_tokens["output_tokens"] == 50
            assert pass2_tokens["input_tokens"] == 120
            assert pass2_tokens["output_tokens"] == 60
