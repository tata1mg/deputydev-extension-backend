"""
Unit tests for QuerySolverAgent base class.

This module provides comprehensive test coverage for the QuerySolverAgent base class
including various method combinations, tool handling, conversation turn conversions,
and edge cases.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from deputydev_core.llm_handler.dataclasses.agent import LLMHandlerInputs
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationRole,
    UnifiedConversationTurnContentType,
    UnifiedImageConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import (
    Attachment,
)
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent import QuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClientTool,
    LLMModel,
    QuerySolverInput,
    Repository,
    ToolUseResponseInput,
)
from test.fixtures.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent_fixtures import *


class TestQuerySolverAgent:
    """Test cases for QuerySolverAgent base class."""

    def test_init(self) -> None:
        """Test QuerySolverAgent initialization."""
        testable_agent = TestableQuerySolverAgent("test_agent", "Test description")
        agent = testable_agent.agent

        assert agent.agent_name == "test_agent"
        assert agent.agent_description == "Test description"
        assert agent.attachment_data_task_map == {}

    def test_generate_conversation_tool_from_client_tool_mcp(
        self, query_solver_input_with_tools: QuerySolverInput
    ) -> None:
        """Test generation of ConversationTool from ClientTool with MCP metadata."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        client_tool = query_solver_input_with_tools.client_tools[0]
        conversation_tool = agent.generate_conversation_tool_from_client_tool(client_tool)

        assert conversation_tool.name == "test_tool"
        assert "test_server" in conversation_tool.description
        assert "Test tool description" in conversation_tool.description
        assert "third party MCP server" in conversation_tool.description
        assert conversation_tool.input_schema.type == "object"
        assert conversation_tool.input_schema.properties == {}

    def test_generate_conversation_tool_from_client_tool_unsupported(self, unsupported_client_tool: ClientTool) -> None:
        """Test generation of ConversationTool with unsupported metadata raises error."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        with pytest.raises(ValueError, match="Unsupported tool metadata type"):
            agent.generate_conversation_tool_from_client_tool(unsupported_client_tool)

    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ConfigManager")
    def test_get_all_first_party_tools_full_features(
        self, mock_config: MagicMock, base_query_solver_input: QuerySolverInput, mock_client_data: ClientData
    ) -> None:
        """Test get_all_first_party_tools with all features enabled."""
        mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": True}

        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        tools = agent.get_all_first_party_tools(base_query_solver_input, mock_client_data)

        tool_names = [tool.name for tool in tools]

        # Check that all expected tools are present
        assert "ask_user_input" in tool_names
        assert "focused_snippets_searcher" in tool_names
        assert "file_path_searcher" in tool_names
        assert "iterative_file_reader" in tool_names
        assert "grep_search" in tool_names
        assert "execute_command" in tool_names
        assert "public_url_content_reader" in tool_names
        assert "related_code_searcher" in tool_names  # embedding_done=True
        assert "get_usage_tool" in tool_names  # lsp_ready=True
        assert "resolve_import_tool" in tool_names  # lsp_ready=True
        assert "create_new_workspace" in tool_names
        assert "replace_in_file" in tool_names  # write_mode=True
        assert "write_to_file" in tool_names  # write_mode=True

    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ConfigManager")
    def test_get_all_first_party_tools_read_only(
        self, mock_config: MagicMock, query_solver_input_read_only: QuerySolverInput, mock_client_data: ClientData
    ) -> None:
        """Test get_all_first_party_tools with read-only mode."""
        mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": False}

        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        tools = agent.get_all_first_party_tools(query_solver_input_read_only, mock_client_data)

        tool_names = [tool.name for tool in tools]

        # Check basic tools are present
        assert "ask_user_input" in tool_names
        assert "focused_snippets_searcher" in tool_names
        assert "iterative_file_reader" in tool_names

        # Check that write tools are not present
        assert "replace_in_file" not in tool_names
        assert "write_to_file" not in tool_names

        # Check that optional tools are not present
        assert "related_code_searcher" not in tool_names  # embedding_done=False
        assert "web_search" not in tool_names  # search_web=False
        assert "get_usage_tool" not in tool_names  # lsp_ready=False
        assert "resolve_import_tool" not in tool_names  # lsp_ready=False

    def test_get_all_client_tools(
        self, query_solver_input_with_tools: QuerySolverInput, mock_client_data: ClientData
    ) -> None:
        """Test get_all_client_tools method."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        tools = agent.get_all_client_tools(query_solver_input_with_tools, mock_client_data)

        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert "test_server" in tools[0].description

    def test_get_all_client_tools_empty(
        self, base_query_solver_input: QuerySolverInput, mock_client_data: ClientData
    ) -> None:
        """Test get_all_client_tools with no client tools."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        tools = agent.get_all_client_tools(base_query_solver_input, mock_client_data)

        assert len(tools) == 0

    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ConfigManager")
    def test_get_all_tools(
        self, mock_config: MagicMock, query_solver_input_with_tools: QuerySolverInput, mock_client_data: ClientData
    ) -> None:
        """Test get_all_tools combines first-party and client tools."""
        mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": True}

        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        tools = agent.get_all_tools(query_solver_input_with_tools, mock_client_data)

        tool_names = [tool.name for tool in tools]

        # Check first-party tools are present
        assert "ask_user_input" in tool_names
        assert "focused_snippets_searcher" in tool_names

        # Check client tool is present
        assert "test_tool" in tool_names

    def test_get_repository_context_single_repo(self, sample_repositories: List[Repository]) -> None:
        """Test get_repository_context with single working repository."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        working_only = [repo for repo in sample_repositories if repo.is_working_repository]
        context = agent.get_repository_context(working_only)

        assert "working_repo" in context
        assert "/path/to/working/repo" in context
        assert "src/" in context
        assert "working_repository" in context
        assert "context_repositories" in context

    def test_get_repository_context_with_context_repos(self, sample_repositories: List[Repository]) -> None:
        """Test get_repository_context with working and context repositories."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        context = agent.get_repository_context(sample_repositories)

        assert "working_repo" in context
        assert "context_repo" in context
        assert "/path/to/working/repo" in context
        assert "/path/to/context/repo" in context
        assert "context_repository_1" in context

    @pytest.mark.asyncio
    async def test_get_unified_user_conv_turns_simple(self, text_message_data_simple: TextMessageData) -> None:
        """Test _get_unified_user_conv_turns with simple text message."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = await agent._get_unified_user_conv_turns(text_message_data_simple)

        assert len(turns) == 1
        assert isinstance(turns[0], UserConversationTurn)
        assert turns[0].role == UnifiedConversationRole.USER
        assert len(turns[0].content) == 1
        assert turns[0].content[0].type == UnifiedConversationTurnContentType.TEXT
        assert "Simple test message" in turns[0].content[0].text

    @pytest.mark.asyncio
    async def test_get_unified_user_conv_turns_with_attachments(
        self, text_message_data_with_attachments: TextMessageData, mock_attachment_task_map: Dict[int, asyncio.Future]
    ) -> None:
        """Test _get_unified_user_conv_turns with attachments."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent
        agent.attachment_data_task_map = mock_attachment_task_map

        turns = await agent._get_unified_user_conv_turns(text_message_data_with_attachments)

        # Should have image turn and text turn
        assert len(turns) == 2

        # First turn should be image
        assert isinstance(turns[0], UserConversationTurn)
        assert turns[0].content[0].type == UnifiedConversationTurnContentType.IMAGE
        assert isinstance(turns[0].content[0], UnifiedImageConversationTurnContent)
        assert turns[0].content[0].image_mimetype == "image/png"

        # Second turn should be text
        assert isinstance(turns[1], UserConversationTurn)
        assert turns[1].content[0].type == UnifiedConversationTurnContentType.TEXT
        assert "Message with attachment" in turns[1].content[0].text
        assert "test vscode environment" in turns[1].content[0].text

    @pytest.mark.asyncio
    async def test_convert_text_agent_chat_to_conversation_turn_user(self, agent_chat_user_text: AgentChatDTO) -> None:
        """Test _convert_text_agent_chat_to_conversation_turn for user messages."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = await agent._convert_text_agent_chat_to_conversation_turn(agent_chat_user_text)

        assert len(turns) == 1
        assert isinstance(turns[0], UserConversationTurn)
        assert turns[0].role == UnifiedConversationRole.USER
        assert "User message" in turns[0].content[0].text

    @pytest.mark.asyncio
    async def test_convert_text_agent_chat_to_conversation_turn_assistant(
        self, agent_chat_assistant_text: AgentChatDTO
    ) -> None:
        """Test _convert_text_agent_chat_to_conversation_turn for assistant messages."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = await agent._convert_text_agent_chat_to_conversation_turn(agent_chat_assistant_text)

        assert len(turns) == 1
        assert isinstance(turns[0], AssistantConversationTurn)
        assert turns[0].role == UnifiedConversationRole.ASSISTANT
        assert turns[0].content[0].text == "Assistant response"

    @pytest.mark.asyncio
    async def test_convert_text_agent_chat_to_conversation_turn_invalid_data(self) -> None:
        """Test _convert_text_agent_chat_to_conversation_turn with invalid message data."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        invalid_chat = AgentChatDTO(
            id=100,
            session_id=1,
            query_id="test_query_id",
            actor=ActorType.USER,
            message_type=ChatMessageType.TEXT,
            message_data=ToolUseMessageData(
                tool_use_id="tool_123", tool_name="test_tool", tool_input={}, tool_response={}
            ),
            metadata={},
            previous_queries=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Expected message_data to be of type TextMessageData"):
            await agent._convert_text_agent_chat_to_conversation_turn(invalid_chat)

    def test_convert_tool_use_agent_chat_to_conversation_turn(self, agent_chat_tool_use: AgentChatDTO) -> None:
        """Test _convert_tool_use_agent_chat_to_conversation_turn with response."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = agent._convert_tool_use_agent_chat_to_conversation_turn(agent_chat_tool_use)

        assert len(turns) == 2

        # First turn should be tool request
        assert isinstance(turns[0], AssistantConversationTurn)
        assert turns[0].role == UnifiedConversationRole.ASSISTANT
        assert turns[0].content[0].type == UnifiedConversationTurnContentType.TOOL_REQUEST
        tool_request = turns[0].content[0]
        assert isinstance(tool_request, UnifiedToolRequestConversationTurnContent)
        assert tool_request.tool_use_id == "tool_123"
        assert tool_request.tool_name == "test_tool"
        assert tool_request.tool_input == {"param": "value"}

        # Second turn should be tool response
        assert isinstance(turns[1], ToolConversationTurn)
        assert turns[1].role == UnifiedConversationRole.TOOL
        assert turns[1].content[0].type == UnifiedConversationTurnContentType.TOOL_RESPONSE
        tool_response = turns[1].content[0]
        assert isinstance(tool_response, UnifiedToolResponseConversationTurnContent)
        assert tool_response.tool_use_id == "tool_123"
        assert tool_response.tool_name == "test_tool"
        assert tool_response.tool_use_response == {"result": "success"}

    def test_convert_tool_use_agent_chat_to_conversation_turn_no_response(
        self, agent_chat_tool_use_no_response: AgentChatDTO
    ) -> None:
        """Test _convert_tool_use_agent_chat_to_conversation_turn without response."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = agent._convert_tool_use_agent_chat_to_conversation_turn(agent_chat_tool_use_no_response)

        assert len(turns) == 2

        # Tool response should have NO_RESPONSE
        tool_response = turns[1].content[0]
        assert isinstance(tool_response, UnifiedToolResponseConversationTurnContent)
        assert tool_response.tool_use_response == {"response": "NO_RESPONSE"}

    def test_convert_tool_use_agent_chat_to_conversation_turn_invalid_data(self) -> None:
        """Test _convert_tool_use_agent_chat_to_conversation_turn with invalid message data."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        invalid_chat = AgentChatDTO(
            id=101,
            session_id=1,
            query_id="test_query_id",
            actor=ActorType.ASSISTANT,
            message_type=ChatMessageType.TOOL_USE,
            message_data=TextMessageData(
                text="Invalid data type",
                attachments=[],
                focus_items=[],
                vscode_env=None,
                repositories=[],
            ),
            metadata={},
            previous_queries=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Expected message_data to be of type ToolUseMessageData"):
            agent._convert_tool_use_agent_chat_to_conversation_turn(invalid_chat)

    def test_convert_thinking_agent_chat_to_conversation_turn(self, agent_chat_thinking: AgentChatDTO) -> None:
        """Test _convert_thinking_agent_chat_to_conversation_turn."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = agent._convert_thinking_agent_chat_to_conversation_turn(agent_chat_thinking)

        assert len(turns) == 1
        assert isinstance(turns[0], AssistantConversationTurn)
        assert turns[0].role == UnifiedConversationRole.ASSISTANT
        assert turns[0].content[0].text == "Thinking about the problem"

    def test_convert_thinking_agent_chat_to_conversation_turn_ignored(
        self, agent_chat_thinking_ignored: AgentChatDTO
    ) -> None:
        """Test _convert_thinking_agent_chat_to_conversation_turn with ignored thinking."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = agent._convert_thinking_agent_chat_to_conversation_turn(agent_chat_thinking_ignored)

        assert len(turns) == 0

    def test_convert_thinking_agent_chat_to_conversation_turn_invalid_data(self) -> None:
        """Test _convert_thinking_agent_chat_to_conversation_turn with invalid message data."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        invalid_chat = AgentChatDTO(
            id=102,
            session_id=1,
            query_id="test_query_id",
            actor=ActorType.ASSISTANT,
            message_type=ChatMessageType.THINKING,
            message_data=TextMessageData(
                text="Invalid data type",
                attachments=[],
                focus_items=[],
                vscode_env=None,
                repositories=[],
            ),
            metadata={},
            previous_queries=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Expected message_data to be of type ThinkingInfoData"):
            agent._convert_thinking_agent_chat_to_conversation_turn(invalid_chat)

    def test_convert_code_block_agent_chat_to_conversation_turn(self, agent_chat_code_block: AgentChatDTO) -> None:
        """Test _convert_code_block_agent_chat_to_conversation_turn."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        turns = agent._convert_code_block_agent_chat_to_conversation_turn(agent_chat_code_block)

        assert len(turns) == 1
        assert isinstance(turns[0], AssistantConversationTurn)
        assert turns[0].role == UnifiedConversationRole.ASSISTANT
        assert "def test_function():" in turns[0].content[0].text

    def test_convert_code_block_agent_chat_to_conversation_turn_invalid_data(self) -> None:
        """Test _convert_code_block_agent_chat_to_conversation_turn with invalid message data."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        invalid_chat = AgentChatDTO(
            id=103,
            session_id=1,
            query_id="test_query_id",
            actor=ActorType.ASSISTANT,
            message_type=ChatMessageType.CODE_BLOCK,
            message_data=TextMessageData(
                text="Invalid data type",
                attachments=[],
                focus_items=[],
                vscode_env=None,
                repositories=[],
            ),
            metadata={},
            previous_queries=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Expected message_data to be of type CodeBlockData"):
            agent._convert_code_block_agent_chat_to_conversation_turn(invalid_chat)

    @pytest.mark.asyncio
    async def test_convert_agent_chats_to_conversation_turns(
        self,
        agent_chat_user_text: AgentChatDTO,
        agent_chat_assistant_text: AgentChatDTO,
        agent_chat_tool_use: AgentChatDTO,
        agent_chat_thinking: AgentChatDTO,
        agent_chat_code_block: AgentChatDTO,
    ) -> None:
        """Test _convert_agent_chats_to_conversation_turns with mixed message types."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        agent_chats = [
            agent_chat_user_text,
            agent_chat_assistant_text,
            agent_chat_tool_use,
            agent_chat_thinking,
            agent_chat_code_block,
        ]

        turns = await agent._convert_agent_chats_to_conversation_turns(agent_chats)

        # User text: 1 turn, Assistant text: 1 turn, Tool use: 2 turns, Thinking: 1 turn, Code block: 1 turn
        assert len(turns) >= 6  # At least 6 turns

        # Check that we have the right mix of turn types
        user_turns = [turn for turn in turns if isinstance(turn, UserConversationTurn)]
        assistant_turns = [turn for turn in turns if isinstance(turn, AssistantConversationTurn)]
        tool_turns = [turn for turn in turns if isinstance(turn, ToolConversationTurn)]

        assert len(user_turns) >= 1
        assert len(assistant_turns) >= 3  # assistant text, thinking, code block
        assert len(tool_turns) >= 1  # tool response

    @pytest.mark.asyncio
    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ChatAttachmentsRepository")
    async def test_get_all_chat_attachments(self, mock_repo: MagicMock, agent_chat_user_text: AgentChatDTO) -> None:
        """Test get_all_chat_attachments method."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        # Mock the repository response
        mock_attachment = MagicMock()
        mock_attachment.id = 123
        mock_attachment.status = "active"
        mock_repo.get_attachments_by_ids = AsyncMock(return_value=[mock_attachment])

        # Add attachment to the chat
        agent_chat_user_text.message_data.attachments = [Attachment(attachment_id=123)]

        attachments = await agent.get_all_chat_attachments([agent_chat_user_text])

        assert len(attachments) == 1
        assert attachments[0].attachment_id == 123
        mock_repo.get_attachments_by_ids.assert_called_once_with([123])

    @pytest.mark.asyncio
    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ChatAttachmentsRepository")
    async def test_get_all_chat_attachments_filtered(
        self, mock_repo: MagicMock, agent_chat_user_text: AgentChatDTO
    ) -> None:
        """Test get_all_chat_attachments filters deleted attachments."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        # Mock the repository response with deleted attachment
        mock_attachment = MagicMock()
        mock_attachment.id = 123
        mock_attachment.status = "deleted"
        mock_repo.get_attachments_by_ids = AsyncMock(return_value=[mock_attachment])

        # Add attachment to the chat
        agent_chat_user_text.message_data.attachments = [Attachment(attachment_id=123)]

        attachments = await agent.get_all_chat_attachments([agent_chat_user_text])

        assert len(attachments) == 0  # Deleted attachment should be filtered out

    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ChatHistoryHandler")
    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ChatFileUpload")
    async def test_get_conversation_turns_and_previous_queries_tool_response(
        self,
        mock_chat_file_upload: MagicMock,
        mock_chat_history_handler: MagicMock,
        agent_query_solver_agent: QuerySolverAgent,
        mock_tool_response_input: ToolUseResponseInput,
    ) -> None:
        """Test _get_conversation_turns_and_previous_queries with new query."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        # Mock the handler
        mock_handler_instance = MagicMock()
        mock_handler_instance.get_relevant_previous_agent_chats_for_new_query = AsyncMock(
            return_value=([agent_chat_user_text], ["previous query"])
        )
        mock_chat_history_handler.return_value = mock_handler_instance

        # Mock ChatFileUpload
        mock_chat_file_upload.get_attachment_data_task_map.return_value = {}

        with patch.object(agent, "get_all_chat_attachments", return_value=[]) as mock_get_attachments:
            turns, previous_queries = await agent._get_conversation_turns_and_previous_queries(
                base_query_solver_input, mock_client_data, agent_chat_user_text
            )

            assert len(previous_queries) == 1
            assert previous_queries[0] == "previous query"
            mock_handler_instance.get_relevant_previous_agent_chats_for_new_query.assert_called_once_with(
                agent_chat_user_text
            )
            mock_get_attachments.assert_called_once_with([agent_chat_user_text])

    @pytest.mark.asyncio
    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ChatHistoryHandler")
    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ChatFileUpload")
    async def test_get_conversation_turns_and_previous_queries_tool_response(
        self,
        mock_chat_file_upload: MagicMock,
        mock_chat_history_handler: MagicMock,
        mock_client_data: ClientData,
    ) -> None:
        """Test _get_conversation_turns_and_previous_queries for tool response submission."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        # Create input without query (tool response scenario)
        payload = QuerySolverInput(
            query=None,  # No query indicates tool response
            session_id=1,
            user_team_id=1,
            session_type="test_session",
            llm_model=LLMModel.CLAUDE_3_POINT_7_SONNET,
            is_embedding_done=True,
            search_web=False,
            is_lsp_ready=True,
            write_mode=True,
            client_tools=[],
        )

        # Mock the handler
        mock_handler_instance = MagicMock()
        mock_handler_instance.get_relevant_previous_agent_chats_for_tool_response_submission = AsyncMock(
            return_value=([], ["tool query"])
        )
        mock_chat_history_handler.return_value = mock_handler_instance

        # Mock ChatFileUpload
        mock_chat_file_upload.get_attachment_data_task_map.return_value = {}

        with patch.object(agent, "get_all_chat_attachments", return_value=[]) as mock_get_attachments:
            turns, previous_queries = await agent._get_conversation_turns_and_previous_queries(
                payload, mock_client_data
            )

            assert len(previous_queries) == 1
            assert previous_queries[0] == "tool query"
            mock_handler_instance.get_relevant_previous_agent_chats_for_tool_response_submission.assert_called_once()
            mock_get_attachments.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_get_conversation_turns_and_previous_queries_missing_new_query_chat(
        self, base_query_solver_input: QuerySolverInput, mock_client_data: ClientData
    ) -> None:
        """Test _get_conversation_turns_and_previous_queries raises error when new_query_chat is missing."""
        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        with pytest.raises(ValueError, match="new_query_chat must be provided when payload.query is present"):
            await agent._get_conversation_turns_and_previous_queries(base_query_solver_input, mock_client_data, None)

    @pytest.mark.asyncio
    @patch("app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent.ConfigManager")
    async def test_get_llm_inputs_and_previous_queries(
        self,
        mock_config: MagicMock,
        base_query_solver_input: QuerySolverInput,
        mock_client_data: ClientData,
        agent_chat_user_text: AgentChatDTO,
    ) -> None:
        """Test get_llm_inputs_and_previous_queries integration."""
        mock_config.configs = {"IS_RELATED_CODE_SEARCHER_ENABLED": True}

        testable_agent = TestableQuerySolverAgent()
        agent = testable_agent.agent

        # Mock the prompt factory with a proper BasePrompt subclass
        from typing import List

        from deputydev_core.llm_handler.dataclasses.main import NonStreamingResponse, UserAndSystemMessages
        from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
        from pydantic import BaseModel

        class MockPrompt(BasePrompt):
            model_name = LLModels.CLAUDE_3_POINT_7_SONNET
            prompt_type = "test_prompt"
            prompt_category = "test_category"

            def __init__(self, params: Dict[Any, Any] = None) -> None:
                super().__init__(params or {})

            def get_prompt(self) -> UserAndSystemMessages:
                return UserAndSystemMessages(user_messages=["Test user message"], system_message="Test system message")

            @classmethod
            def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Any]:
                return ["mock result"]

            @classmethod
            async def get_parsed_response_blocks(cls, response_block: List[Any]) -> List[BaseModel]:
                return []

        agent.prompt_factory.get_prompt.return_value = MockPrompt

        with patch.object(agent, "_get_conversation_turns_and_previous_queries") as mock_get_turns:
            mock_get_turns.return_value = ([], ["previous query"])

            llm_inputs, previous_queries = await agent.get_llm_inputs_and_previous_queries(
                base_query_solver_input, mock_client_data, LLModels.CLAUDE_3_POINT_7_SONNET, agent_chat_user_text
            )

            assert isinstance(llm_inputs, LLMHandlerInputs)
            assert len(llm_inputs.tools) > 0  # Should have tools
            assert llm_inputs.prompt == MockPrompt
            assert llm_inputs.messages == []
            assert len(previous_queries) == 1
            assert previous_queries[0] == "previous query"

            mock_get_turns.assert_called_once_with(
                base_query_solver_input, mock_client_data, agent_chat_user_text, None
            )
            agent.prompt_factory.get_prompt.assert_called_once_with(model_name=LLModels.CLAUDE_3_POINT_7_SONNET)
