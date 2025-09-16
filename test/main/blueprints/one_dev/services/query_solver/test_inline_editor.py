"""
Unit tests for InlineEditGenerator.

This module provides comprehensive test coverage for the InlineEditGenerator class
including various input combinations, conversation handling, LLM responses,
and edge cases.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationRole,
    UnifiedConversationTurnContentType,
    UserConversationTurn,
)
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    CodeBlockData,
    MessageType,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.inline_editor import InlineEditGenerator
from test.fixtures.main.blueprints.one_dev.services.query_solver.inline_editor_fixtures import *


class TestInlineEditGenerator:
    """Test cases for InlineEditGenerator class."""

    @pytest.mark.asyncio
    async def test_get_conversation_turns_from_agent_chat_user_message(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_agent_chat_user: AgentChatDTO,
    ) -> None:
        """Test conversion of user agent chat to conversation turns."""
        with patch(
            "app.main.blueprints.one_dev.services.query_solver.inline_editor.PromptFeatureFactory"
        ) as mock_factory:
            # Create a mock prompt handler that when called returns an object with get_prompt method
            mock_prompt_class = MagicMock()
            mock_prompt_instance = MagicMock()
            mock_prompt_result = MagicMock()
            mock_prompt_result.user_message = "Generate improved code with error handling"
            mock_prompt_instance.get_prompt.return_value = mock_prompt_result
            mock_prompt_class.return_value = mock_prompt_instance
            mock_factory.get_prompt.return_value = mock_prompt_class

            conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
                agent_chats=[mock_agent_chat_user], llm_model=LLModels.CLAUDE_3_POINT_7_SONNET
            )

            assert len(conversation_turns) == 1
            assert isinstance(conversation_turns[0], UserConversationTurn)
            assert conversation_turns[0].role == UnifiedConversationRole.USER
            assert len(conversation_turns[0].content) == 1
            assert conversation_turns[0].content[0].text == "Generate improved code with error handling"

    @pytest.mark.asyncio
    async def test_get_conversation_turns_from_agent_chat_assistant_code_block(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_agent_chat_assistant_code: AgentChatDTO,
    ) -> None:
        """Test conversion of assistant code block to conversation turns."""
        conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
            agent_chats=[mock_agent_chat_assistant_code], llm_model=LLModels.CLAUDE_3_POINT_7_SONNET
        )

        assert len(conversation_turns) == 1
        assert isinstance(conversation_turns[0], AssistantConversationTurn)
        assert conversation_turns[0].role == UnifiedConversationRole.ASSISTANT
        assert len(conversation_turns[0].content) == 1
        assert "try:" in conversation_turns[0].content[0].text
        assert "except Exception as e:" in conversation_turns[0].content[0].text

    @pytest.mark.asyncio
    async def test_get_conversation_turns_from_agent_chat_assistant_tool_with_response(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_agent_chat_assistant_tool_with_response: AgentChatDTO,
    ) -> None:
        """Test conversion of assistant tool use with response to conversation turns."""
        conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
            agent_chats=[mock_agent_chat_assistant_tool_with_response], llm_model=LLModels.CLAUDE_3_POINT_7_SONNET
        )

        assert len(conversation_turns) == 2

        # First turn should be assistant tool request
        assert isinstance(conversation_turns[0], AssistantConversationTurn)
        assert conversation_turns[0].role == UnifiedConversationRole.ASSISTANT
        assert len(conversation_turns[0].content) == 1
        assert conversation_turns[0].content[0].type == UnifiedConversationTurnContentType.TOOL_REQUEST
        assert conversation_turns[0].content[0].tool_use_id == "tool_12345"
        assert conversation_turns[0].content[0].tool_name == "replace_in_file"

        # Second turn should be tool response
        assert isinstance(conversation_turns[1], ToolConversationTurn)
        assert conversation_turns[1].role == UnifiedConversationRole.TOOL
        assert len(conversation_turns[1].content) == 1
        assert conversation_turns[1].content[0].type == UnifiedConversationTurnContentType.TOOL_RESPONSE
        assert conversation_turns[1].content[0].tool_use_id == "tool_12345"
        assert conversation_turns[1].content[0].tool_name == "replace_in_file"

    @pytest.mark.asyncio
    async def test_get_conversation_turns_from_agent_chat_mixed(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_agent_chat_user: AgentChatDTO,
        mock_agent_chat_assistant_code: AgentChatDTO,
        mock_agent_chat_assistant_tool_with_response: AgentChatDTO,
    ) -> None:
        """Test conversion of mixed agent chats to conversation turns."""
        with patch(
            "app.main.blueprints.one_dev.services.query_solver.inline_editor.PromptFeatureFactory"
        ) as mock_factory:
            # Create a mock prompt handler that when called returns an object with get_prompt method
            mock_prompt_class = MagicMock()
            mock_prompt_instance = MagicMock()
            mock_prompt_result = MagicMock()
            mock_prompt_result.user_message = "Generate improved code with error handling"
            mock_prompt_instance.get_prompt.return_value = mock_prompt_result
            mock_prompt_class.return_value = mock_prompt_instance
            mock_factory.get_prompt.return_value = mock_prompt_class

            conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
                agent_chats=[
                    mock_agent_chat_user,
                    mock_agent_chat_assistant_code,
                    mock_agent_chat_assistant_tool_with_response,
                ],
                llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
            )

            assert len(conversation_turns) == 4
            assert isinstance(conversation_turns[0], UserConversationTurn)
            assert isinstance(conversation_turns[1], AssistantConversationTurn)
            assert isinstance(conversation_turns[2], AssistantConversationTurn)
            assert isinstance(conversation_turns[3], ToolConversationTurn)

    @pytest.mark.asyncio
    async def test_get_response_from_parsed_llm_response_with_code(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_llm_response_with_code: Any,
    ) -> None:
        """Test processing LLM response with code snippets."""
        with patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo:
            mock_repo.create_chat = AsyncMock()

            result = await inline_edit_generator._get_response_from_parsed_llm_response(
                parsed_llm_response=mock_llm_response_with_code.parsed_content,
                query_id="test_query_123",
                session_id=123,
                llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
            )

            assert result["code_snippets"] is not None
            assert len(result["code_snippets"]) == 1
            assert result["code_snippets"][0]["programming_language"] == "python"
            assert "try:" in result["code_snippets"][0]["code"]
            assert result["tool_use_request"] is None

            # Verify agent chat was created
            mock_repo.create_chat.assert_called_once()
            call_args = mock_repo.create_chat.call_args[1]["chat_data"]
            assert call_args.message_type == MessageType.CODE_BLOCK
            assert isinstance(call_args.message_data, CodeBlockData)

    @pytest.mark.asyncio
    async def test_get_response_from_parsed_llm_response_with_tool_use(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_llm_response_with_tool_use: Any,
    ) -> None:
        """Test processing LLM response with tool use request."""
        with patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo:
            mock_repo.create_chat = AsyncMock()

            result = await inline_edit_generator._get_response_from_parsed_llm_response(
                parsed_llm_response=mock_llm_response_with_tool_use.parsed_content,
                query_id="test_query_123",
                session_id=123,
                llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
            )

            assert result["code_snippets"] is None
            assert result["tool_use_request"] is not None
            assert result["tool_use_request"]["content"]["tool_name"] == "replace_in_file"
            assert result["tool_use_request"]["content"]["tool_use_id"] == "tool_12345"

            # Verify agent chat was created
            mock_repo.create_chat.assert_called_once()
            call_args = mock_repo.create_chat.call_args[1]["chat_data"]
            assert call_args.message_type == MessageType.TOOL_USE
            assert isinstance(call_args.message_data, ToolUseMessageData)

    @pytest.mark.asyncio
    async def test_get_response_from_parsed_llm_response_mixed(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_llm_response_mixed: Any,
    ) -> None:
        """Test processing LLM response with both code snippets and tool use."""
        with patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo:
            mock_repo.create_chat = AsyncMock()

            result = await inline_edit_generator._get_response_from_parsed_llm_response(
                parsed_llm_response=mock_llm_response_mixed.parsed_content,
                query_id="test_query_123",
                session_id=123,
                llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
            )

            assert result["code_snippets"] is not None
            assert len(result["code_snippets"]) == 1
            assert result["tool_use_request"] is not None
            assert result["tool_use_request"]["content"]["tool_use_id"] == "tool_67890"

            # Verify two agent chats were created
            assert mock_repo.create_chat.call_count == 2

    @pytest.mark.asyncio
    async def test_get_response_from_parsed_llm_response_empty(
        self,
        inline_edit_generator: InlineEditGenerator,
        empty_llm_response: Any,
    ) -> None:
        """Test processing empty LLM response."""
        with patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo:
            mock_repo.create_chat = AsyncMock()

            result = await inline_edit_generator._get_response_from_parsed_llm_response(
                parsed_llm_response=empty_llm_response.parsed_content,
                query_id="test_query_123",
                session_id=123,
                llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
            )

            assert result["code_snippets"] is None
            assert result["tool_use_request"] is None

            # Verify no agent chats were created
            mock_repo.create_chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_new_query(
        self,
        inline_edit_generator: InlineEditGenerator,
        basic_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
        mock_llm_response_with_code: Any,
    ) -> None:
        """Test getting inline edit diff suggestion for new query."""
        with (
            patch(
                "app.main.blueprints.one_dev.services.query_solver.inline_editor.LLMHandler"
            ) as mock_llm_handler_class,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.ConfigManager") as mock_config,
        ):
            # Setup mocks
            mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": False}
            mock_llm_handler = MagicMock()
            mock_llm_handler.start_llm_query = AsyncMock(return_value=mock_llm_response_with_code)
            mock_llm_handler_class.return_value = mock_llm_handler

            mock_created_chat = MagicMock()
            mock_created_chat.query_id = "test_query_123"
            mock_repo.create_chat = AsyncMock(return_value=mock_created_chat)

            result = await inline_edit_generator.get_inline_edit_diff_suggestion(
                payload=basic_inline_edit_input, client_data=mock_client_data
            )

            assert result["code_snippets"] is not None
            assert len(result["code_snippets"]) == 1
            assert result["tool_use_request"] is None

            # Verify user chat was created (this is the first call - USER chat)
            # The second call is the ASSISTANT chat with code snippets
            assert mock_repo.create_chat.call_count >= 1
            first_call_args = mock_repo.create_chat.call_args_list[0][1]["chat_data"]
            assert first_call_args.actor == ActorType.USER
            assert first_call_args.message_type == MessageType.TEXT
            assert isinstance(first_call_args.message_data, TextMessageData)
            assert first_call_args.message_data.text == "Add error handling to this function"

            # Verify LLM was called
            mock_llm_handler.start_llm_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_with_tool_response(
        self,
        inline_edit_generator: InlineEditGenerator,
        inline_edit_input_with_tool_response: InlineEditInput,
        mock_client_data: ClientData,
        mock_agent_chat_assistant_tool: AgentChatDTO,
        mock_llm_response_with_code: Any,
    ) -> None:
        """Test getting inline edit diff suggestion with tool use response."""
        with (
            patch(
                "app.main.blueprints.one_dev.services.query_solver.inline_editor.LLMHandler"
            ) as mock_llm_handler_class,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.ConfigManager") as mock_config,
        ):
            # Setup mocks
            mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": False}
            mock_llm_handler = MagicMock()
            mock_llm_handler.start_llm_query = AsyncMock(return_value=mock_llm_response_with_code)
            mock_llm_handler_class.return_value = mock_llm_handler

            mock_repo.get_chats_by_session_id = AsyncMock(return_value=[mock_agent_chat_assistant_tool])
            mock_repo.update_chat = AsyncMock()
            mock_repo.create_chat = AsyncMock()

            result = await inline_edit_generator.get_inline_edit_diff_suggestion(
                payload=inline_edit_input_with_tool_response, client_data=mock_client_data
            )

            assert result["code_snippets"] is not None
            assert len(result["code_snippets"]) == 1

            # Verify tool response was updated
            mock_repo.update_chat.assert_called_once()

            # Verify LLM was called with conversation turns
            mock_llm_handler.start_llm_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_tool_response_no_matching_chat(
        self,
        inline_edit_generator: InlineEditGenerator,
        inline_edit_input_with_tool_response: InlineEditInput,
        mock_client_data: ClientData,
    ) -> None:
        """Test getting inline edit diff suggestion with tool response but no matching chat."""
        with patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo:
            mock_repo.get_chats_by_session_id = AsyncMock(return_value=[])

            with pytest.raises(ValueError, match="No matching agent chat found"):
                await inline_edit_generator.get_inline_edit_diff_suggestion(
                    payload=inline_edit_input_with_tool_response, client_data=mock_client_data
                )

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_gpt_4_model(
        self,
        inline_edit_generator: InlineEditGenerator,
        gpt_4_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
        mock_llm_response_with_code: Any,
    ) -> None:
        """Test getting inline edit diff suggestion with GPT-4 model (includes task completion tool)."""
        with (
            patch(
                "app.main.blueprints.one_dev.services.query_solver.inline_editor.LLMHandler"
            ) as mock_llm_handler_class,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.ConfigManager") as mock_config,
        ):
            # Setup mocks
            mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": False}
            mock_llm_handler = MagicMock()
            mock_llm_handler.start_llm_query = AsyncMock(return_value=mock_llm_response_with_code)
            mock_llm_handler_class.return_value = mock_llm_handler

            mock_created_chat = MagicMock()
            mock_created_chat.query_id = "test_query_123"
            mock_repo.create_chat = AsyncMock(return_value=mock_created_chat)

            result = await inline_edit_generator.get_inline_edit_diff_suggestion(
                payload=gpt_4_inline_edit_input, client_data=mock_client_data
            )

            assert result["code_snippets"] is not None

            # Verify LLM was called with required tool choice
            mock_llm_handler.start_llm_query.assert_called_once()
            call_kwargs = mock_llm_handler.start_llm_query.call_args[1]
            assert call_kwargs["tool_choice"] == "required"
            # GPT-4 should include TASK_COMPLETION tool
            tool_names = [tool.name for tool in call_kwargs["tools"]]
            assert "task_completion" in tool_names

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_invalid_input(
        self,
        inline_edit_generator: InlineEditGenerator,
        invalid_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
    ) -> None:
        """Test getting inline edit diff suggestion with invalid input."""
        with pytest.raises(ValueError, match="Either query and code selection or tool use response must be provided"):
            await inline_edit_generator.get_inline_edit_diff_suggestion(
                payload=invalid_inline_edit_input, client_data=mock_client_data
            )

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_non_streaming_response_error(
        self,
        inline_edit_generator: InlineEditGenerator,
        basic_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
    ) -> None:
        """Test error when LLM response is not NonStreamingParsedLLMCallResponse."""
        with (
            patch(
                "app.main.blueprints.one_dev.services.query_solver.inline_editor.LLMHandler"
            ) as mock_llm_handler_class,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.ConfigManager") as mock_config,
        ):
            # Setup mocks
            mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": False}
            mock_llm_handler = MagicMock()
            mock_llm_handler.start_llm_query = AsyncMock(return_value="invalid_response")
            mock_llm_handler_class.return_value = mock_llm_handler

            mock_created_chat = MagicMock()
            mock_created_chat.query_id = "test_query_123"
            mock_repo.create_chat = AsyncMock(return_value=mock_created_chat)

            with pytest.raises(ValueError, match="LLM response is not of type NonStreamingParsedLLMCallResponse"):
                await inline_edit_generator.get_inline_edit_diff_suggestion(
                    payload=basic_inline_edit_input, client_data=mock_client_data
                )

    @pytest.mark.asyncio
    async def test_start_job_success(
        self,
        inline_edit_generator: InlineEditGenerator,
        basic_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
    ) -> None:
        """Test successful job start."""
        mock_result = {
            "code_snippets": [{"code": "test_code", "programming_language": "python", "file_path": "/test.py"}],
            "tool_use_request": None,
        }

        with (
            patch.object(
                inline_edit_generator, "get_inline_edit_diff_suggestion", return_value=mock_result
            ) as mock_get,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.JobService") as mock_job_service,
        ):
            mock_job_service.db_update = AsyncMock()

            await inline_edit_generator.start_job(
                payload=basic_inline_edit_input, job_id=123, client_data=mock_client_data
            )

            mock_get.assert_called_once_with(payload=basic_inline_edit_input, client_data=mock_client_data)
            mock_job_service.db_update.assert_called_once_with(
                {"id": 123}, {"status": "COMPLETED", "final_output": mock_result}
            )

    @pytest.mark.asyncio
    async def test_start_job_failure(
        self,
        inline_edit_generator: InlineEditGenerator,
        basic_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
    ) -> None:
        """Test job start with failure."""
        with (
            patch.object(
                inline_edit_generator, "get_inline_edit_diff_suggestion", side_effect=Exception("Test error")
            ) as mock_get,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.JobService") as mock_job_service,
        ):
            mock_job_service.db_update = AsyncMock()

            await inline_edit_generator.start_job(
                payload=basic_inline_edit_input, job_id=123, client_data=mock_client_data
            )

            mock_get.assert_called_once_with(payload=basic_inline_edit_input, client_data=mock_client_data)
            mock_job_service.db_update.assert_called_once_with(
                {"id": 123}, {"status": "FAILED", "final_output": {"error": "Test error"}}
            )

    @pytest.mark.asyncio
    async def test_create_and_start_job(
        self,
        inline_edit_generator: InlineEditGenerator,
        basic_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
        mock_job_dto: Any,
    ) -> None:
        """Test creating and starting a job."""
        with (
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.JobService") as mock_job_service,
            patch.object(inline_edit_generator, "start_job") as mock_start_job,
            patch("asyncio.create_task") as mock_create_task,
        ):
            mock_job_service.db_create = AsyncMock(return_value=mock_job_dto)

            result = await inline_edit_generator.create_and_start_job(
                payload=basic_inline_edit_input, client_data=mock_client_data
            )

            assert result == mock_job_dto.id

            # Verify job was created
            mock_job_service.db_create.assert_called_once()
            call_args = mock_job_service.db_create.call_args[0][0]
            assert call_args.type == "INLINE_EDIT"
            assert call_args.session_id == "123"
            assert call_args.user_team_id == basic_inline_edit_input.auth_data.user_team_id
            assert call_args.status == "PENDING"

            # Verify task was created
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_conversation_turns_empty_agent_chats(
        self,
        inline_edit_generator: InlineEditGenerator,
    ) -> None:
        """Test getting conversation turns from empty agent chats."""
        conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
            agent_chats=[], llm_model=LLModels.CLAUDE_3_POINT_7_SONNET
        )

        assert len(conversation_turns) == 0

    @pytest.mark.asyncio
    async def test_get_conversation_turns_user_without_focus_items(
        self,
        inline_edit_generator: InlineEditGenerator,
    ) -> None:
        """Test getting conversation turns from user chat without focus items."""
        mock_chat = AgentChatDTO(
            id=1,
            session_id=123,
            actor=ActorType.USER,
            message_type=MessageType.TEXT,
            message_data=TextMessageData(
                text="Add error handling to this function",
                focus_items=[],  # Empty focus items
            ),
            query_id="test_query_123",
            metadata={"is_inline_editor": True, "llm_model": "CLAUDE_3_POINT_7_SONNET"},
            previous_queries=[],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        with patch(
            "app.main.blueprints.one_dev.services.query_solver.inline_editor.PromptFeatureFactory"
        ) as mock_factory:
            # Create a mock prompt handler that when called returns an object with get_prompt method
            mock_prompt_class = MagicMock()
            mock_prompt_instance = MagicMock()
            mock_prompt_result = MagicMock()
            mock_prompt_result.user_message = "Generate improved code with error handling"
            mock_prompt_instance.get_prompt.return_value = mock_prompt_result
            mock_prompt_class.return_value = mock_prompt_instance
            mock_factory.get_prompt.return_value = mock_prompt_class

            conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
                agent_chats=[mock_chat], llm_model=LLModels.CLAUDE_3_POINT_7_SONNET
            )

            assert len(conversation_turns) == 1
            assert isinstance(conversation_turns[0], UserConversationTurn)

            # Verify prompt handler was called with None code_selection
            mock_factory.get_prompt.assert_called_once()
            # Check that get_prompt was called correctly and the prompt class was called with correct args
            mock_prompt_class.assert_called_once()
            call_args = mock_prompt_class.call_args[0][0]  # First argument is the prompt vars dict
            assert call_args["code_selection"] is None

    @pytest.mark.asyncio
    async def test_get_conversation_turns_assistant_tool_without_response(
        self,
        inline_edit_generator: InlineEditGenerator,
        mock_agent_chat_assistant_tool: AgentChatDTO,
    ) -> None:
        """Test getting conversation turns from assistant tool without response."""
        conversation_turns = await inline_edit_generator._get_conversation_turns_from_agent_chat_for_inline_edit(
            agent_chats=[mock_agent_chat_assistant_tool], llm_model=LLModels.CLAUDE_3_POINT_7_SONNET
        )

        # Should have no conversation turns because tool_response is None in the agent chat
        # The code only creates turns for tool use messages when tool_response exists
        assert len(conversation_turns) == 0

    @pytest.mark.asyncio
    async def test_get_inline_edit_diff_suggestion_with_related_code_searcher(
        self,
        inline_edit_generator: InlineEditGenerator,
        basic_inline_edit_input: InlineEditInput,
        mock_client_data: ClientData,
        mock_llm_response_with_code: Any,
    ) -> None:
        """Test getting inline edit diff suggestion with related code searcher enabled."""
        with (
            patch(
                "app.main.blueprints.one_dev.services.query_solver.inline_editor.LLMHandler"
            ) as mock_llm_handler_class,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.AgentChatsRepository") as mock_repo,
            patch("app.main.blueprints.one_dev.services.query_solver.inline_editor.ConfigManager") as mock_config,
        ):
            # Setup mocks - enable related code searcher
            mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": True}
            mock_llm_handler = MagicMock()
            mock_llm_handler.start_llm_query = AsyncMock(return_value=mock_llm_response_with_code)
            mock_llm_handler_class.return_value = mock_llm_handler

            mock_created_chat = MagicMock()
            mock_created_chat.query_id = "test_query_123"
            mock_repo.create_chat = AsyncMock(return_value=mock_created_chat)

            result = await inline_edit_generator.get_inline_edit_diff_suggestion(
                payload=basic_inline_edit_input, client_data=mock_client_data
            )

            assert result["code_snippets"] is not None

            # Verify LLM was called with related code searcher tool
            mock_llm_handler.start_llm_query.assert_called_once()
            call_kwargs = mock_llm_handler.start_llm_query.call_args[1]
            tool_names = [tool.name for tool in call_kwargs["tools"]]
            assert "related_code_searcher" in tool_names
