"""
Unit tests for BaseCommenterAgent.

This module contains comprehensive unit tests for the BaseCommenterAgent class,
testing all methods including initialization, tool handling, agent execution logic,
payload processing, conversation handling, and edge cases.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationTool,
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.main.blueprints.deputy_dev.models.dto.review_agent_chats_dto import (
    ActorType,
    MessageType,
    ReviewAgentChatDTO,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor import (
    BaseCommenterAgent,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commenter_agent_fixtures import *


# Concrete implementation of BaseCommenterAgent for testing
class TestCommenterAgent(BaseCommenterAgent):
    """Test implementation of BaseCommenterAgent."""

    agent_type = AgentTypes.SECURITY
    agent_name = "test_security_commenter"
    is_dual_pass = False
    prompt_features = [PromptFeatures.SECURITY_COMMENTS_GENERATION]


class TestDualPassCommenterAgent(BaseCommenterAgent):
    """Test implementation of BaseCommenterAgent with dual pass."""

    agent_type = AgentTypes.CODE_COMMUNICATION
    agent_name = "test_communication_commenter"
    is_dual_pass = True
    prompt_features = [
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_1,
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_2,
    ]


class TestBaseCommenterAgentInitialization:
    """Test BaseCommenterAgent initialization."""

    def test_init_with_user_agent_dto(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test initialization with UserAgentDTO."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        assert agent.context_service == mock_context_service
        assert agent.llm_handler == mock_llm_handler
        assert agent.model == LLModels.GPT_4O
        assert agent.agent_id == sample_user_agent_dto.id
        assert agent.agent_name == sample_user_agent_dto.agent_name
        assert agent.display_name == sample_user_agent_dto.display_name
        assert agent.tool_request_manager is not None
        assert agent.review_agent_chats == []
        assert agent.prompt_vars == {}

        # Check agent_setting dictionary
        expected_setting = {
            "agent_id": sample_user_agent_dto.id,
            "display_name": sample_user_agent_dto.display_name,
            "objective": sample_user_agent_dto.objective,
            "custom_prompt": sample_user_agent_dto.custom_prompt,
            "confidence_score": sample_user_agent_dto.confidence_score,
        }
        assert agent.agent_setting == expected_setting

    def test_init_with_default_display_name(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, user_agent_dto_no_display_name: UserAgentDTO
    ) -> None:
        """Test initialization when display_name is None - should use agent_type.value."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=user_agent_dto_no_display_name,
        )

        assert agent.display_name == TestCommenterAgent.agent_type.value
        assert agent.agent_setting["display_name"] == TestCommenterAgent.agent_type.value

    def test_init_dual_pass_agent(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test initialization of dual pass agent."""
        agent = TestDualPassCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        assert agent.is_dual_pass
        assert len(agent.prompt_features) == 2
        assert agent.agent_type == AgentTypes.CODE_COMMUNICATION


class TestBaseCommenterAgentAgentRelevantChunk:
    """Test BaseCommenterAgent agent_relevant_chunk method."""

    def test_agent_relevant_chunk_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        sample_relevant_chunks: Dict[str, Any],
    ) -> None:
        """Test agent_relevant_chunk returns rendered snippet array."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.render_snippet_array"
        ) as mock_render:
            mock_render.return_value = "rendered snippet"

            result = agent.agent_relevant_chunk(sample_relevant_chunks)

            assert result == "rendered snippet"
            mock_render.assert_called_once()

    def test_agent_relevant_chunk_empty_mapping(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        empty_relevant_chunks: Dict[str, Any],
    ) -> None:
        """Test agent_relevant_chunk with empty chunk mapping."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.render_snippet_array"
        ) as mock_render:
            mock_render.return_value = ""

            result = agent.agent_relevant_chunk(empty_relevant_chunks)

            assert result == ""


class TestBaseCommenterAgentRequiredPromptVariables:
    """Test BaseCommenterAgent required_prompt_variables method."""

    @pytest.mark.asyncio
    async def test_required_prompt_variables_success(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test required_prompt_variables returns expected variables."""

        # Set up separate return values for the two different calls
        async def mock_get_pr_diff(append_line_no_info: bool = False):
            if append_line_no_info:
                return "diff with line numbers"
            else:
                return "diff without line numbers"

        mock_context_service.get_pr_diff.side_effect = mock_get_pr_diff

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        result = await agent.required_prompt_variables()

        expected = {
            "PULL_REQUEST_DIFF": "diff with line numbers",
            "PR_DIFF_WITHOUT_LINE_NUMBER": "diff without line numbers",
            "AGENT_OBJECTIVE": sample_user_agent_dto.objective,
            "CUSTOM_PROMPT": sample_user_agent_dto.custom_prompt,
            "AGENT_NAME": TestCommenterAgent.agent_type.value,
        }

        assert result == expected
        assert mock_context_service.get_pr_diff.call_count == 2

    @pytest.mark.asyncio
    async def test_required_prompt_variables_with_last_pass_result(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test required_prompt_variables with last_pass_result parameter."""

        # Set up separate return values for the two different calls
        async def mock_get_pr_diff_integration(append_line_no_info: bool = False):
            if append_line_no_info:
                return "diff with line numbers"
            else:
                return "diff without line numbers"

        mock_context_service.get_pr_diff.side_effect = mock_get_pr_diff_integration

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        last_pass_result = {"previous": "result"}
        result = await agent.required_prompt_variables(last_pass_result)

        # Should return same result regardless of last_pass_result
        expected = {
            "PULL_REQUEST_DIFF": "diff with line numbers",
            "PR_DIFF_WITHOUT_LINE_NUMBER": "diff without line numbers",
            "AGENT_OBJECTIVE": sample_user_agent_dto.objective,
            "CUSTOM_PROMPT": sample_user_agent_dto.custom_prompt,
            "AGENT_NAME": TestCommenterAgent.agent_type.value,
        }

        assert result == expected

    @pytest.mark.asyncio
    async def test_required_prompt_variables_empty_agent_setting(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, user_agent_dto_minimal: UserAgentDTO
    ) -> None:
        """Test required_prompt_variables with minimal agent setting."""
        mock_context_service.get_pr_diff.side_effect = ["diff with line numbers", "diff without line numbers"]

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=user_agent_dto_minimal,
        )

        result = await agent.required_prompt_variables()

        expected = {
            "PULL_REQUEST_DIFF": "diff with line numbers",
            "PR_DIFF_WITHOUT_LINE_NUMBER": "diff without line numbers",
            "AGENT_OBJECTIVE": user_agent_dto_minimal.objective,  # Will be None
            "CUSTOM_PROMPT": user_agent_dto_minimal.custom_prompt or "",  # Will be ""
            "AGENT_NAME": TestCommenterAgent.agent_type.value,
        }

        assert result == expected


class TestBaseCommenterAgentGetDisplayName:
    """Test BaseCommenterAgent get_display_name method."""

    def test_get_display_name_with_custom_name(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test get_display_name returns custom display name."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        result = agent.get_display_name()
        assert result == sample_user_agent_dto.display_name

    def test_get_display_name_fallback_to_agent_type(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, user_agent_dto_no_display_name: UserAgentDTO
    ) -> None:
        """Test get_display_name falls back to agent type when no display name."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=user_agent_dto_no_display_name,
        )

        result = agent.get_display_name()
        assert result == TestCommenterAgent.agent_type.value


class TestBaseCommenterAgentGetConversationTurnsFromChat:
    """Test BaseCommenterAgent _get_conversation_turns_from_chat method."""

    def test_get_conversation_turns_from_text_messages(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        sample_review_agent_chat_text: List[ReviewAgentChatDTO],
    ) -> None:
        """Test conversion of text message chats to conversation turns."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        result = agent._get_conversation_turns_from_chat(sample_review_agent_chat_text)

        assert len(result) == 1
        # Should create UserConversationTurn for REVIEW_AGENT text messages
        assert hasattr(result[0], "content")
        assert len(result[0].content) == 1

    def test_get_conversation_turns_from_tool_messages(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        sample_review_agent_chat_tool: List[ReviewAgentChatDTO],
    ) -> None:
        """Test conversion of tool message chats to conversation turns."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        result = agent._get_conversation_turns_from_chat(sample_review_agent_chat_tool)

        # Should create AssistantConversationTurn for ASSISTANT tool messages
        # And ToolConversationTurn if tool_response exists
        assert len(result) >= 1

    def test_get_conversation_turns_empty_list(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test conversion with empty chat list."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        result = agent._get_conversation_turns_from_chat([])

        assert result == []


class TestBaseCommenterAgentGetToolsForReview:
    """Test BaseCommenterAgent get_tools_for_review method."""

    def test_get_tools_for_review_tools_enabled(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        mock_prompt_handler_tools_enabled: MagicMock,
    ) -> None:
        """Test get_tools_for_review when tools are enabled."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch.object(agent.tool_request_manager, "get_tools") as mock_get_tools:
            mock_tools = [MagicMock(spec=ConversationTool)]
            mock_get_tools.return_value = mock_tools

            result = agent.get_tools_for_review(mock_prompt_handler_tools_enabled)

            assert result == mock_tools
            mock_get_tools.assert_called_once()

    def test_get_tools_for_review_tools_disabled(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        mock_prompt_handler_tools_disabled: MagicMock,
    ) -> None:
        """Test get_tools_for_review when tools are disabled."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.PARSE_FINAL_RESPONSE"
        ) as mock_final_response:
            result = agent.get_tools_for_review(mock_prompt_handler_tools_disabled)

            assert result == [mock_final_response]


class TestBaseCommenterAgentRunAgent:
    """Test BaseCommenterAgent run_agent method."""

    @pytest.mark.asyncio
    async def test_run_agent_query_request_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
    ) -> None:
        """Test run_agent with query request type."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Mock the _handle_query_request method
        expected_result = AgentRunResult(
            agent_result=None,
            prompt_tokens_exceeded=True,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        with (
            patch.object(agent, "_handle_query_request", return_value=expected_result) as mock_handle_query,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])

            result = await agent.run_agent(valid_session_id, query_payload)

            assert result == expected_result
            mock_handle_query.assert_called_once_with(valid_session_id, query_payload)
            mock_repo.get_chats_by_agent_id_and_session.assert_called_once_with(
                session_id=valid_session_id, agent_id=str(sample_user_agent_dto.id)
            )

    @pytest.mark.asyncio
    async def test_run_agent_tool_use_response_request(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        tool_use_response_payload: Dict[str, Any],
    ) -> None:
        """Test run_agent with tool_use_response request type."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        expected_result = AgentRunResult(
            agent_result={"tool_result": "success"},
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        with (
            patch.object(agent, "_handle_tool_use_response", return_value=expected_result) as mock_handle_tool,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])

            result = await agent.run_agent(valid_session_id, tool_use_response_payload)

            assert result == expected_result
            mock_handle_tool.assert_called_once_with(valid_session_id, tool_use_response_payload)

    @pytest.mark.asyncio
    async def test_run_agent_tool_use_failed_request(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        tool_use_failed_payload: Dict[str, Any],
    ) -> None:
        """Test run_agent with tool_use_failed request type."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        expected_result = AgentRunResult(
            agent_result={"status": "error"},
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        with (
            patch.object(agent, "_handle_tool_use_response", return_value=expected_result) as mock_handle_tool,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])

            result = await agent.run_agent(valid_session_id, tool_use_failed_payload)

            assert result == expected_result
            mock_handle_tool.assert_called_once_with(valid_session_id, tool_use_failed_payload)

    @pytest.mark.asyncio
    async def test_run_agent_invalid_request_type(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        invalid_payload: Dict[str, Any],
    ) -> None:
        """Test run_agent with invalid request type."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
        ) as mock_repo:
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])

            with pytest.raises(ValueError, match="Invalid request type: invalid_type"):
                await agent.run_agent(valid_session_id, invalid_payload)

    @pytest.mark.asyncio
    async def test_run_agent_no_payload(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
    ) -> None:
        """Test run_agent with no payload (should default to empty dict)."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
        ) as mock_repo:
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])

            with pytest.raises(ValueError, match="Invalid request type: None"):
                await agent.run_agent(valid_session_id)

    @pytest.mark.asyncio
    async def test_run_agent_with_existing_chats(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
        sample_review_agent_chat_text: List[ReviewAgentChatDTO],
    ) -> None:
        """Test run_agent loads existing chats."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        expected_result = AgentRunResult(
            agent_result={"status": "success"},
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        with (
            patch.object(agent, "_handle_query_request", return_value=expected_result),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=sample_review_agent_chat_text)

            await agent.run_agent(valid_session_id, query_payload)

            assert agent.review_agent_chats == sample_review_agent_chat_text


class TestBaseCommenterAgentHandleQueryRequest:
    """Test BaseCommenterAgent _handle_query_request method."""

    @pytest.mark.asyncio
    async def test_handle_query_request_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
    ) -> None:
        """Test successful _handle_query_request."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        expected_result = AgentRunResult(
            agent_result={"status": "success"},
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        # Setup the expected chats that will be created and added to review_agent_chats
        cached_chat = MagicMock(spec=ReviewAgentChatDTO)
        cached_chat.message_data = MagicMock(spec=TextMessageData)
        cached_chat.message_data.message_type = MessageType.TEXT
        cached_chat.message_data.text = "cached message"
        cached_chat.actor = ActorType.REVIEW_AGENT
        cached_chat.metadata = {"cache_breakpoint": True}

        query_chat = MagicMock(spec=ReviewAgentChatDTO)
        query_chat.message_data = MagicMock(spec=TextMessageData)
        query_chat.message_data.message_type = MessageType.TEXT
        query_chat.message_data.text = "query message"
        query_chat.actor = ActorType.REVIEW_AGENT
        query_chat.metadata = {}

        with (
            patch.object(agent, "_process_llm_response", return_value=expected_result) as mock_process,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.create_chat = AsyncMock(side_effect=[cached_chat, query_chat])

            result = await agent._handle_query_request(valid_session_id, query_payload)

            assert result == expected_result
            mock_process.assert_called_once()
            # Should create two chats: cached and query
            assert mock_repo.create_chat.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_query_request_token_limit_exceeded(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
        mock_prompt_handler: MagicMock,
    ) -> None:
        """Test _handle_query_request when token limit is exceeded."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler

        with patch.object(agent, "has_exceeded_token_limit", return_value=True):
            result = await agent._handle_query_request(valid_session_id, query_payload)

            assert result.prompt_tokens_exceeded is True
            assert result.agent_result is None
            # LLM handler should not be called when token limit exceeded
            mock_llm_handler.start_llm_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_query_request_invalid_llm_response(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
        mock_prompt_handler: MagicMock,
        invalid_llm_response: MagicMock,
    ) -> None:
        """Test _handle_query_request with invalid LLM response type."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = invalid_llm_response

        # Setup the expected chats that will be created and added to review_agent_chats
        cached_chat = MagicMock(spec=ReviewAgentChatDTO)
        cached_chat.message_data = MagicMock(spec=TextMessageData)
        cached_chat.message_data.message_type = MessageType.TEXT
        cached_chat.message_data.text = "cached message"
        cached_chat.actor = ActorType.REVIEW_AGENT
        cached_chat.metadata = {"cache_breakpoint": True}

        query_chat = MagicMock(spec=ReviewAgentChatDTO)
        query_chat.message_data = MagicMock(spec=TextMessageData)
        query_chat.message_data.message_type = MessageType.TEXT
        query_chat.message_data.text = "query message"
        query_chat.actor = ActorType.REVIEW_AGENT
        query_chat.metadata = {}

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
        ) as mock_repo:
            mock_repo.create_chat = AsyncMock(side_effect=[cached_chat, query_chat])

            with pytest.raises(ValueError, match="LLM Response is not of type NonStreamingParsedLLMCallResponse"):
                await agent._handle_query_request(valid_session_id, query_payload)


class TestBaseCommenterAgentHandleToolUseResponse:
    """Test BaseCommenterAgent _handle_tool_use_response method."""

    @pytest.mark.asyncio
    async def test_handle_tool_use_response_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        tool_use_response_payload: Dict[str, Any],
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
    ) -> None:
        """Test successful _handle_tool_use_response."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup existing chat with matching tool_use_id
        existing_chat = MagicMock(spec=ReviewAgentChatDTO)
        existing_chat.message_data = MagicMock(spec=ToolUseMessageData)
        existing_chat.message_data.message_type = MessageType.TOOL_USE
        existing_chat.message_data.tool_use_id = "test_tool_use_id"
        existing_chat.message_data.tool_name = "iterative_file_reader"
        existing_chat.message_data.tool_input = {"param": "value"}
        existing_chat.message_data.tool_response = {"result": "success"}
        existing_chat.actor = ActorType.ASSISTANT
        existing_chat.id = 123
        agent.review_agent_chats = [existing_chat]

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        expected_result = AgentRunResult(
            agent_result={"tool_result": "success"},
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        with (
            patch.object(agent, "_process_llm_response", return_value=expected_result) as mock_process,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.update_chat = AsyncMock()

            result = await agent._handle_tool_use_response(valid_session_id, tool_use_response_payload)

            assert result == expected_result
            mock_process.assert_called_once()
            mock_repo.update_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_use_response_missing_tool_response(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
    ) -> None:
        """Test _handle_tool_use_response with missing tool_use_response."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        payload = {"type": "tool_use_response"}  # Missing tool_use_response

        with pytest.raises(ValueError, match="tool_use_response is required in payload"):
            await agent._handle_tool_use_response(valid_session_id, payload)

    @pytest.mark.asyncio
    async def test_handle_tool_use_response_tool_failed(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        tool_use_failed_payload: Dict[str, Any],
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
    ) -> None:
        """Test _handle_tool_use_response with failed tool."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        expected_result = AgentRunResult(
            agent_result=None,
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
            is_finished=True,
        )

        with patch.object(agent, "_process_llm_response", return_value=expected_result):
            result = await agent._handle_tool_use_response(valid_session_id, tool_use_failed_payload)

            assert result == expected_result

    @pytest.mark.asyncio
    async def test_handle_tool_use_response_invalid_llm_response(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        tool_use_response_payload: Dict[str, Any],
        mock_prompt_handler: MagicMock,
        invalid_llm_response: MagicMock,
    ) -> None:
        """Test _handle_tool_use_response with invalid LLM response."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = invalid_llm_response

        with pytest.raises(ValueError, match="Invalid LLM response"):
            await agent._handle_tool_use_response(valid_session_id, tool_use_response_payload)


class TestBaseCommenterAgentProcessLLMResponse:
    """Test BaseCommenterAgent _process_llm_response method."""

    @pytest.mark.asyncio
    async def test_process_llm_response_final_response_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        sample_llm_response_final: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
        sample_final_response: Dict[str, Any],
    ) -> None:
        """Test _process_llm_response with final response."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with (
            patch.object(agent.tool_request_manager, "is_final_response", return_value=True),
            patch.object(agent.tool_request_manager, "extract_final_response", return_value=sample_final_response),
            patch.object(agent, "_save_comments_to_db") as mock_save,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.create_chat = AsyncMock(return_value=MagicMock(spec=ReviewAgentChatDTO))

            result = await agent._process_llm_response(
                sample_llm_response_final, valid_session_id, [], mock_prompt_handler, {}
            )

            assert result.agent_result["status"] == "success"
            assert result.agent_result["message"] == "Review completed successfully"
            mock_save.assert_called_once_with(sample_final_response)

    @pytest.mark.asyncio
    async def test_process_llm_response_final_response_error(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        sample_llm_response_final: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
    ) -> None:
        """Test _process_llm_response with final response processing error."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with (
            patch.object(agent.tool_request_manager, "is_final_response", return_value=True),
            patch.object(
                agent.tool_request_manager, "extract_final_response", side_effect=Exception("Processing error")
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.AppLogger"
            ),
        ):
            result = await agent._process_llm_response(
                sample_llm_response_final, valid_session_id, [], mock_prompt_handler, {}
            )

            assert result.agent_result["status"] == "error"
            assert "Processing error" in result.agent_result["message"]

    @pytest.mark.asyncio
    async def test_process_llm_response_tool_request(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
        sample_tool_request: Dict[str, Any],
    ) -> None:
        """Test _process_llm_response with tool request."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with (
            patch.object(agent.tool_request_manager, "is_final_response", return_value=False),
            patch.object(agent.tool_request_manager, "is_review_planner_response", return_value=False),
            patch.object(agent.tool_request_manager, "parse_tool_use_request", return_value=sample_tool_request),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.create_chat = AsyncMock(return_value=MagicMock(spec=ReviewAgentChatDTO))

            result = await agent._process_llm_response(
                sample_llm_response, valid_session_id, [], mock_prompt_handler, {}
            )

            assert result.agent_result == sample_tool_request
            mock_repo.create_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_llm_response_no_tool_request(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
    ) -> None:
        """Test _process_llm_response with no tool request found."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with (
            patch.object(agent.tool_request_manager, "is_final_response", return_value=False),
            patch.object(agent.tool_request_manager, "is_review_planner_response", return_value=False),
            patch.object(agent.tool_request_manager, "parse_tool_use_request", return_value=None),
        ):
            result = await agent._process_llm_response(
                sample_llm_response, valid_session_id, [], mock_prompt_handler, {}
            )

            assert result.agent_result["status"] == "error"
            assert "No valid tool use request found" in result.agent_result["message"]


class TestBaseCommenterAgentSaveCommentsToDb:
    """Test BaseCommenterAgent _save_comments_to_db method."""

    @pytest.mark.asyncio
    async def test_save_comments_to_db_success(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        sample_final_response_with_comments: Dict[str, Any],
    ) -> None:
        """Test _save_comments_to_db with valid comments."""
        mock_context_service.review_id = 123

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.IdeCommentRepository"
        ) as mock_repo:
            mock_repo.insert_comments = AsyncMock()

            await agent._save_comments_to_db(sample_final_response_with_comments)

            mock_repo.insert_comments.assert_called_once()
            # Verify the call was made with a list of IdeReviewsCommentDTO
            call_args = mock_repo.insert_comments.call_args[0][0]
            assert isinstance(call_args, list)
            assert len(call_args) == 2  # Based on fixture

    @pytest.mark.asyncio
    async def test_save_comments_to_db_empty_comments(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test _save_comments_to_db with empty comments."""
        mock_context_service.review_id = 123

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        final_response = {"comments": []}

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.IdeCommentRepository"
        ) as mock_repo:
            mock_repo.insert_comments = AsyncMock()

            await agent._save_comments_to_db(final_response)

            # Should not call insert_comments for empty list
            mock_repo.insert_comments.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_comments_to_db_no_comments_key(
        self, mock_context_service: MagicMock, mock_llm_handler: MagicMock, sample_user_agent_dto: UserAgentDTO
    ) -> None:
        """Test _save_comments_to_db with no comments key."""
        mock_context_service.review_id = 123

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        final_response = {"other_data": "value"}

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.IdeCommentRepository"
        ) as mock_repo:
            mock_repo.insert_comments = AsyncMock()

            await agent._save_comments_to_db(final_response)

            # Should not call insert_comments for empty list
            mock_repo.insert_comments.assert_not_called()


class TestBaseCommenterAgentEdgeCases:
    """Test BaseCommenterAgent edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_run_agent_with_zero_session_id(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        query_payload: Dict[str, Any],
        zero_session_id: int,
    ) -> None:
        """Test run_agent with zero session ID."""
        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        expected_result = AgentRunResult(
            agent_result={"status": "success"},
            prompt_tokens_exceeded=False,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            model=agent.model.value,
            tokens_data={},
            display_name=agent.get_display_name(),
        )

        with (
            patch.object(agent, "_handle_query_request", return_value=expected_result),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_repo,
        ):
            mock_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])

            result = await agent.run_agent(zero_session_id, query_payload)

            assert result == expected_result
            mock_repo.get_chats_by_agent_id_and_session.assert_called_once_with(
                session_id=zero_session_id, agent_id=str(sample_user_agent_dto.id)
            )

    def test_agent_with_all_llm_models(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        all_llm_models: List[LLModels],
    ) -> None:
        """Test agent initialization with all available LLM models."""
        for model in all_llm_models:
            agent = TestCommenterAgent(
                context_service=mock_context_service,
                llm_handler=mock_llm_handler,
                model=model,
                user_agent_dto=sample_user_agent_dto,
            )
            assert agent.model == model

    def test_agent_with_all_agent_types(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        all_agent_types: List[AgentTypes],
    ) -> None:
        """Test agent initialization with all available agent types."""
        for agent_type_enum in all_agent_types:

            def create_dynamic_commenter(agent_type_val: AgentTypes) -> type:
                class DynamicTestCommenterAgent(BaseCommenterAgent):
                    agent_type = agent_type_val
                    agent_name = f"test_{agent_type_val.value}_commenter"
                    is_dual_pass = False
                    prompt_features = [PromptFeatures.SECURITY_COMMENTS_GENERATION]

                return DynamicTestCommenterAgent

            DynamicTestCommenterAgent = create_dynamic_commenter(agent_type_enum)

            agent = DynamicTestCommenterAgent(
                context_service=mock_context_service,
                llm_handler=mock_llm_handler,
                model=LLModels.GPT_4O,
                user_agent_dto=sample_user_agent_dto,
            )

            assert agent.agent_type == agent_type_enum
            assert agent.agent_name == sample_user_agent_dto.agent_name  # Gets set from DTO, not class attribute


class TestBaseCommenterAgentIntegration:
    """Test BaseCommenterAgent integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_commenter_workflow_query_to_final_response(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
        sample_llm_response_final: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
        sample_final_response_with_comments: Dict[str, Any],
    ) -> None:
        """Test complete commenter workflow from query to final response."""
        mock_context_service.review_id = 123
        mock_context_service.get_pr_diff.side_effect = ["diff with line numbers", "diff without line numbers"]

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response_final

        # Setup the expected chats that will be created and added to review_agent_chats
        cached_chat = MagicMock(spec=ReviewAgentChatDTO)
        cached_chat.message_data = MagicMock(spec=TextMessageData)
        cached_chat.message_data.message_type = MessageType.TEXT
        cached_chat.message_data.text = "cached message"
        cached_chat.actor = ActorType.REVIEW_AGENT
        cached_chat.metadata = {"cache_breakpoint": True}

        query_chat = MagicMock(spec=ReviewAgentChatDTO)
        query_chat.message_data = MagicMock(spec=TextMessageData)
        query_chat.message_data.message_type = MessageType.TEXT
        query_chat.message_data.text = "query message"
        query_chat.actor = ActorType.REVIEW_AGENT
        query_chat.metadata = {}

        with (
            patch.object(agent.tool_request_manager, "is_final_response", return_value=True),
            patch.object(
                agent.tool_request_manager, "extract_final_response", return_value=sample_final_response_with_comments
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
            ) as mock_chat_repo,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.IdeCommentRepository"
            ) as mock_comment_repo,
        ):
            mock_chat_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])
            mock_chat_repo.create_chat = AsyncMock(side_effect=[cached_chat, query_chat])
            mock_comment_repo.insert_comments = AsyncMock()

            result = await agent.run_agent(valid_session_id, query_payload)

            # Verify complete workflow
            assert result.agent_result["status"] == "success"
            assert result.agent_result["message"] == "Review completed successfully"
            assert result.prompt_tokens_exceeded is False
            assert result.agent_name == agent.agent_name
            assert result.agent_type == agent.agent_type
            assert result.display_name == agent.get_display_name()

            # Verify chats were created
            assert mock_chat_repo.create_chat.call_count >= 2  # cached + query chats

            # Verify comments were saved
            mock_comment_repo.insert_comments.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_commenter_workflow_with_tool_interaction(
        self,
        mock_context_service: MagicMock,
        mock_llm_handler: MagicMock,
        sample_user_agent_dto: UserAgentDTO,
        valid_session_id: int,
        query_payload: Dict[str, Any],
        sample_llm_response: NonStreamingParsedLLMCallResponse,
        mock_prompt_handler: MagicMock,
        sample_tool_request: Dict[str, Any],
    ) -> None:
        """Test complete commenter workflow with tool interaction (simplified)."""
        mock_context_service.review_id = 123

        # Set up separate return values for the two different calls
        async def mock_get_pr_diff_integration(append_line_no_info: bool = False):
            if append_line_no_info:
                return "diff with line numbers"
            else:
                return "diff without line numbers"

        mock_context_service.get_pr_diff.side_effect = mock_get_pr_diff_integration

        agent = TestCommenterAgent(
            context_service=mock_context_service,
            llm_handler=mock_llm_handler,
            model=LLModels.GPT_4O,
            user_agent_dto=sample_user_agent_dto,
        )

        # Setup mocks for tool request flow
        mock_llm_handler.prompt_handler_map.get_prompt.return_value = lambda x: mock_prompt_handler
        mock_llm_handler.start_llm_query.return_value = sample_llm_response

        # Setup the expected chats that will be created and added to review_agent_chats
        cached_chat = MagicMock(spec=ReviewAgentChatDTO)
        cached_chat.message_data = MagicMock(spec=TextMessageData)
        cached_chat.message_data.message_type = MessageType.TEXT
        cached_chat.message_data.text = "cached message"
        cached_chat.actor = ActorType.REVIEW_AGENT
        cached_chat.metadata = {"cache_breakpoint": True}

        query_chat = MagicMock(spec=ReviewAgentChatDTO)
        query_chat.message_data = MagicMock(spec=TextMessageData)
        query_chat.message_data.message_type = MessageType.TEXT
        query_chat.message_data.text = "query message"
        query_chat.actor = ActorType.REVIEW_AGENT
        query_chat.metadata = {}

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor.ReviewAgentChatsRepository"
        ) as mock_chat_repo:
            mock_chat_repo.get_chats_by_agent_id_and_session = AsyncMock(return_value=[])
            mock_chat_dto = MagicMock(spec=ReviewAgentChatDTO)
            mock_chat_dto.id = 123
            mock_chat_dto.message_data = MagicMock(spec=ToolUseMessageData)
            mock_chat_dto.message_data.message_type = MessageType.TOOL_USE
            mock_chat_dto.message_data.tool_use_id = "test_tool_use_id"
            mock_chat_repo.create_chat = AsyncMock(side_effect=[cached_chat, query_chat, mock_chat_dto])

            # Test: Query request returns tool request
            with (
                patch.object(agent.tool_request_manager, "is_final_response", return_value=False),
                patch.object(agent.tool_request_manager, "is_review_planner_response", return_value=False),
                patch.object(agent.tool_request_manager, "parse_tool_use_request", return_value=sample_tool_request),
            ):
                result = await agent.run_agent(valid_session_id, query_payload)

                # Verify the workflow executed correctly
                assert result.agent_result == sample_tool_request
                assert result.agent_name == agent.agent_name
                assert result.agent_type == agent.agent_type
                assert result.display_name == agent.get_display_name()

                # Verify chats were created
                assert mock_chat_repo.create_chat.call_count == 3  # cached + query + tool chats
