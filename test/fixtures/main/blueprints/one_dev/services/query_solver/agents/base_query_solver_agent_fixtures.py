"""
Fixtures for testing base_query_solver_agent.

This module provides comprehensive fixtures for testing various scenarios
of the QuerySolverAgent class including different input combinations,
mock data, and edge cases.
"""

import asyncio
from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from deputydev_core.llm_handler.dataclasses.main import ConversationTool
from deputydev_core.llm_handler.models.dto.chat_attachments_dto import ChatAttachmentsDTO

from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import (
    Attachment,
    ChatAttachmentDataWithObjectBytes,
)
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    CodeBlockData,
    TextMessageData,
    ThinkingInfoData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClientTool,
    LLMModel,
    MCPToolMetadata,
    QuerySolverInput,
    Repository,
)


class TestableQuerySolverAgent:
    """Testable implementation of QuerySolverAgent for testing purposes."""

    def __init__(self, agent_name: str = "test_agent", agent_description: str = "Test agent"):
        """Initialize the testable agent."""
        # Import here to avoid circular imports
        from app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent import QuerySolverAgent

        # Create a testable subclass
        class ConcreteTestAgent(QuerySolverAgent):
            prompt_factory = MagicMock()
            all_tools = []

        self.agent = ConcreteTestAgent(agent_name, agent_description)


@pytest.fixture
def mock_client_data() -> ClientData:
    """Create mock client data."""
    from deputydev_core.utils.constants.enums import Clients

    return ClientData(
        client=Clients.BACKEND,
        client_version="1.0.0",
    )


@pytest.fixture
def base_query_solver_input() -> QuerySolverInput:
    """Create a basic QuerySolverInput for testing."""
    return QuerySolverInput(
        query="Test query",
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


@pytest.fixture
def query_solver_input_with_tools() -> QuerySolverInput:
    """Create a QuerySolverInput with client tools."""
    mcp_tool_metadata = MCPToolMetadata(server_id="test_server", tool_name="test_tool")
    client_tool = ClientTool(
        name="test_tool",
        description="Test tool description",
        input_schema={"type": "object", "properties": {}},
        tool_metadata=mcp_tool_metadata,
    )

    return QuerySolverInput(
        query="Test query with tools",
        session_id=1,
        user_team_id=1,
        session_type="test_session",
        llm_model=LLMModel.CLAUDE_3_POINT_7_SONNET,
        is_embedding_done=True,
        search_web=True,
        is_lsp_ready=True,
        write_mode=True,
        client_tools=[client_tool],
    )


@pytest.fixture
def query_solver_input_read_only() -> QuerySolverInput:
    """Create a QuerySolverInput for read-only mode."""
    return QuerySolverInput(
        query="Test read-only query",
        session_id=1,
        user_team_id=1,
        session_type="test_session",
        llm_model=LLMModel.CLAUDE_3_POINT_7_SONNET,
        is_embedding_done=False,
        search_web=False,
        is_lsp_ready=False,
        write_mode=False,
        client_tools=[],
    )


@pytest.fixture
def sample_repositories() -> List[Repository]:
    """Create sample repositories for testing."""
    working_repo = Repository(
        repo_path="/path/to/working/repo",
        repo_name="working_repo",
        root_directory_context="src/\ntest/\nREADME.md",
        is_working_repository=True,
    )

    context_repo = Repository(
        repo_path="/path/to/context/repo",
        repo_name="context_repo",
        root_directory_context="lib/\ndocs/\npackage.json",
        is_working_repository=False,
    )

    return [working_repo, context_repo]


@pytest.fixture
def text_message_data_simple() -> TextMessageData:
    """Create simple TextMessageData."""
    return TextMessageData(
        text="Simple test message",
        attachments=[],
        focus_items=[],
        vscode_env=None,
        repositories=[],
    )


@pytest.fixture
def text_message_data_with_attachments() -> TextMessageData:
    """Create TextMessageData with attachments."""
    attachment = Attachment(attachment_id=123)
    return TextMessageData(
        text="Message with attachment",
        attachments=[attachment],
        focus_items=[],
        vscode_env="test vscode environment",
        repositories=[],
    )


@pytest.fixture
def agent_chat_user_text() -> AgentChatDTO:
    """Create a user text AgentChatDTO."""
    return AgentChatDTO(
        id=1,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.USER,
        message_type=ChatMessageType.TEXT,
        message_data=TextMessageData(
            text="User message",
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


@pytest.fixture
def agent_chat_assistant_text() -> AgentChatDTO:
    """Create an assistant text AgentChatDTO."""
    return AgentChatDTO(
        id=2,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.ASSISTANT,
        message_type=ChatMessageType.TEXT,
        message_data=TextMessageData(
            text="Assistant response",
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


@pytest.fixture
def agent_chat_tool_use() -> AgentChatDTO:
    """Create a tool use AgentChatDTO."""
    return AgentChatDTO(
        id=3,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.ASSISTANT,
        message_type=ChatMessageType.TOOL_USE,
        message_data=ToolUseMessageData(
            tool_use_id="tool_123",
            tool_name="test_tool",
            tool_input={"param": "value"},
            tool_response={"result": "success"},
        ),
        metadata={},
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def agent_chat_tool_use_no_response() -> AgentChatDTO:
    """Create a tool use AgentChatDTO without response."""
    return AgentChatDTO(
        id=4,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.ASSISTANT,
        message_type=ChatMessageType.TOOL_USE,
        message_data=ToolUseMessageData(
            tool_use_id="tool_456",
            tool_name="test_tool_no_response",
            tool_input={"param": "value"},
            tool_response=None,
        ),
        metadata={},
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def agent_chat_thinking() -> AgentChatDTO:
    """Create a thinking AgentChatDTO."""
    return AgentChatDTO(
        id=5,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.ASSISTANT,
        message_type=ChatMessageType.THINKING,
        message_data=ThinkingInfoData(
            thinking_summary="Thinking about the problem",
            ignore_in_chat=False,
        ),
        metadata={},
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def agent_chat_thinking_ignored() -> AgentChatDTO:
    """Create a thinking AgentChatDTO that should be ignored."""
    return AgentChatDTO(
        id=6,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.ASSISTANT,
        message_type=ChatMessageType.THINKING,
        message_data=ThinkingInfoData(
            thinking_summary="Hidden thinking",
            ignore_in_chat=True,
        ),
        metadata={},
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def agent_chat_code_block() -> AgentChatDTO:
    """Create a code block AgentChatDTO."""
    return AgentChatDTO(
        id=7,
        session_id=1,
        query_id="test_query_id",
        actor=ActorType.ASSISTANT,
        message_type=ChatMessageType.CODE_BLOCK,
        message_data=CodeBlockData(code="def test_function():\n    return True", language="python"),
        metadata={},
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_chat_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Create mock chat attachment data."""
    from datetime import datetime

    metadata = ChatAttachmentsDTO(
        id=123,
        file_name="test_image.png",
        file_type="image/png",
        s3_key="test/key",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=metadata,
        object_bytes=b"fake_image_data",
    )


@pytest.fixture
def mock_attachment_task_map(mock_chat_attachment_data: ChatAttachmentDataWithObjectBytes) -> Dict[int, asyncio.Future]:
    """Create mock attachment task map."""
    # Create a future with the result already set
    future = asyncio.Future()
    future.set_result(mock_chat_attachment_data)
    return {123: future}


@pytest.fixture
def conversation_tool_sample() -> ConversationTool:
    """Create a sample ConversationTool."""
    return ConversationTool(
        name="sample_tool",
        description="A sample tool for testing",
        input_schema={
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Input parameter"}},
            "required": ["input"],
        },
    )


@pytest.fixture
def unsupported_client_tool() -> ClientTool:
    """Create a ClientTool with unsupported metadata for testing error cases."""
    # We'll create a ClientTool that we'll manually modify to have unsupported metadata

    class UnsupportedMetadata:
        def __init__(self) -> None:
            self.type = "UNSUPPORTED"

    # Create a valid tool first, then change the metadata
    tool = ClientTool(
        name="unsupported_tool",
        description="Tool with unsupported metadata",
        input_schema={"type": "object"},
        tool_metadata=MCPToolMetadata(server_id="test", tool_name="test"),
    )
    # Override with unsupported metadata
    tool.tool_metadata = UnsupportedMetadata()  # type: ignore
    return tool


@pytest.fixture
def mock_config_manager() -> MagicMock:
    """Create a mock ConfigManager."""
    mock_config = MagicMock()
    mock_config.configs = {
        "IS_RELATED_CODE_SEARCHER_ENABLED": True,
    }
    return mock_config


@pytest.fixture
def mock_chat_history_handler() -> MagicMock:
    """Create a mock ChatHistoryHandler."""
    handler = MagicMock()
    handler.get_relevant_previous_agent_chats_for_new_query = AsyncMock(return_value=([], []))
    handler.get_relevant_previous_agent_chats_for_tool_response_submission = AsyncMock(return_value=([], []))
    return handler


@pytest.fixture
def mock_chat_file_upload() -> MagicMock:
    """Create a mock ChatFileUpload."""
    mock_upload = MagicMock()
    mock_upload.get_attachment_data_task_map = MagicMock(return_value={})
    return mock_upload


@pytest.fixture
def mock_chat_attachments_repository() -> MagicMock:
    """Create a mock ChatAttachmentsRepository."""
    repo = MagicMock()
    repo.get_attachments_by_ids = AsyncMock(return_value=[])
    return repo
