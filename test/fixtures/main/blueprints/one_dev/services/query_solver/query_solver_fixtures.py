"""
Fixtures for testing QuerySolver.solve_query method.

This module provides comprehensive fixtures for testing various scenarios
of the solve_query method including different input combinations,
mock data, and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
    StreamingParsedLLMCallResponse,
)
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.constants.tools import ToolStatus

# Import these inside fixtures to avoid configuration issues


@pytest.fixture
def query_solver():
    """Create a QuerySolver instance for testing."""
    # Import here to avoid module-level import issues with Google dependencies
    from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver

    return QuerySolver()


@pytest.fixture
def mock_client_data():
    """Create mock client data."""
    from deputydev_core.utils.constants.enums import Clients

    return ClientData(
        client=Clients.BACKEND,
        client_version="1.0.0",
    )


@pytest.fixture
def mock_llm_handler() -> MagicMock:
    """Create a mock LLM handler."""
    # Import here to avoid module-level import issues with Google dependencies
    from app.backend_common.services.llm.handler import LLMHandler

    handler = MagicMock(spec=LLMHandler)
    handler.start_llm_query = AsyncMock()
    return handler


@pytest.fixture
def mock_streaming_response() -> StreamingParsedLLMCallResponse:
    """Create a mock streaming LLM response."""
    response = MagicMock(spec=StreamingParsedLLMCallResponse)
    response.query_id = "test-query-id"
    response.parsed_content = AsyncMock()
    response.llm_response_storage_task = AsyncMock()
    return response


@pytest.fixture
def mock_non_streaming_response() -> NonStreamingParsedLLMCallResponse:
    """Create a mock non-streaming LLM response."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [{"summary": "Test summary"}]
    return response


@pytest.fixture
def mock_agent_chat_dto():
    """Create a mock AgentChatDTO."""
    from datetime import datetime

    from app.main.blueprints.one_dev.models.dto.agent_chats import (
        ActorType,
        AgentChatDTO,
        TextMessageData,
    )
    from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType

    return AgentChatDTO(
        id=1,
        session_id=123,
        actor=ActorType.USER,
        message_data=TextMessageData(text="Test query"),
        message_type=ChatMessageType.TEXT,
        metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
        query_id="test-query-id",
        previous_queries=[],
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00"),
    )


@pytest.fixture
def mock_tool_use_message_data():
    """Create mock tool use message data."""
    from app.main.blueprints.one_dev.models.dto.agent_chats import ToolUseMessageData

    return ToolUseMessageData(
        tool_use_id="test-tool-use-id",
        tool_name="test_tool",
        tool_input={"param": "value"},
        tool_response=None,
    )


@pytest.fixture
def mock_cancellation_checker():
    """Create a mock cancellation checker."""
    from app.main.blueprints.one_dev.utils.cancellation_checker import CancellationChecker

    checker = MagicMock(spec=CancellationChecker)
    checker.is_cancelled = MagicMock(return_value=False)
    return checker


@pytest.fixture
def basic_query_solver_input():
    """Create a basic QuerySolverInput for testing."""
    from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
    from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
        FileFocusItem,
        FocusItemTypes,
        LLMModel,
        QuerySolverInput,
        Repository,
    )

    return QuerySolverInput(
        query="Test query for basic functionality",
        write_mode=False,
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="linux",
        shell="bash",
        vscode_env="development",
        llm_model=LLMModel.GPT_4_POINT_1,
        deputy_dev_rules="Follow best practices",
        repositories=[
            Repository(
                repo_path="/path/to/repo",
                repo_name="test_repo",
                root_directory_context="test context",
                is_working_repository=True,
            )
        ],
        focus_items=[
            FileFocusItem(
                type=FocusItemTypes.FILE,
                path="/path/to/file.py",
                value="test_file.py",
            )
        ],
        attachments=[
            Attachment(
                attachment_id=1,
            )
        ],
    )


@pytest.fixture
def tool_response_query_solver_input():
    """Create QuerySolverInput with tool responses."""
    from app.main.blueprints.one_dev.constants.tools import ToolStatus
    from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
        QuerySolverInput,
        ToolUseResponseInput,
    )

    return QuerySolverInput(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="linux",
        shell="bash",
        vscode_env="development",
        deputy_dev_rules="Follow best practices",
        batch_tool_responses=[
            ToolUseResponseInput(
                tool_name="test_tool",
                tool_use_id="test-tool-use-id",
                response={"result": "success", "data": "test_data"},
                status=ToolStatus.COMPLETED,
            )
        ],
    )


@pytest.fixture
def reasoning_query_solver_input():
    """Create QuerySolverInput with reasoning parameter."""
    from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import LLMModel, QuerySolverInput

    return QuerySolverInput(
        query="Test query with reasoning",
        write_mode=False,
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="linux",
        shell="bash",
        vscode_env="development",
        llm_model=LLMModel.GPT_4_POINT_1,
        reasoning="MEDIUM",
        deputy_dev_rules="Follow best practices",
    )


@pytest.fixture
def retry_query_solver_input():
    """Create QuerySolverInput with retry reason."""
    return QuerySolverInput(
        query="Test query with retry",
        write_mode=False,
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="linux",
        shell="bash",
        vscode_env="development",
        llm_model=LLMModel.GPT_4_POINT_1,
        retry_reason=RetryReasons.TOOL_USE_FAILED,
        deputy_dev_rules="Follow best practices",
    )


@pytest.fixture
def attachments_focus_query_solver_input():
    """Create QuerySolverInput with attachments and focus items."""
    return QuerySolverInput(
        query="Test query with attachments and focus items",
        write_mode=True,
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="darwin",
        shell="zsh",
        vscode_env="production",
        llm_model=LLMModel.CLAUDE_3_POINT_5_SONNET,
        deputy_dev_rules="Follow best practices and security guidelines",
        attachments=[
            Attachment(
                attachment_id=1,
            ),
            Attachment(
                attachment_id=2,
            ),
        ],
        focus_items=[
            ClassFocusItem(
                type=FocusItemTypes.CLASS,
                path="/path/to/class.py",
                value="TestClass",
                chunks=[],
            ),
            FileFocusItem(
                type=FocusItemTypes.FILE,
                path="/path/to/module.py",
                value="module.py",
            ),
        ],
    )


@pytest.fixture
def empty_query_solver_input():
    """Create empty QuerySolverInput for testing invalid input."""
    from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import QuerySolverInput

    return QuerySolverInput(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
    )


@pytest.fixture
def no_llm_model_query_solver_input():
    """Create QuerySolverInput without LLM model for testing validation."""
    from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import QuerySolverInput

    return QuerySolverInput(
        query="Test query without LLM model",
        session_id=123,
        user_team_id=1,
        session_type="test_session",
    )


@pytest.fixture
def multiple_tool_responses_input():
    """Create QuerySolverInput with multiple tool responses."""
    return QuerySolverInput(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="linux",
        shell="bash",
        vscode_env="development",
        deputy_dev_rules="Follow best practices",
        batch_tool_responses=[
            ToolUseResponseInput(
                tool_name="file_reader",
                tool_use_id="tool-1",
                response={"content": "File content 1"},
                status=ToolStatus.COMPLETED,
            ),
            ToolUseResponseInput(
                tool_name="code_searcher",
                tool_use_id="tool-2",
                response={"results": ["match1", "match2"]},
                status=ToolStatus.COMPLETED,
            ),
            ToolUseResponseInput(
                tool_name="write_file",
                tool_use_id="tool-3",
                response={"status": "written", "path": "/tmp/output.py"},
                status=ToolStatus.COMPLETED,
            ),
        ],
    )


@pytest.fixture
def tool_response_with_retry_input():
    """Create QuerySolverInput with tool response and retry reason."""
    return QuerySolverInput(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        os_name="linux",
        shell="bash",
        vscode_env="development",
        deputy_dev_rules="Follow best practices",
        llm_model=LLMModel(name="gpt-4", value="gpt-4"),
        retry_reason=RetryReasons.THROTTLED,
        reasoning="detailed",
        batch_tool_responses=[
            ToolUseResponseInput(
                tool_name="failing_tool",
                tool_use_id="retry-tool-id",
                response={"error": "Previous attempt failed"},
                status=ToolStatus.FAILED,
            )
        ],
    )


@pytest.fixture
def mock_tool_responses_batch():
    """Create a batch of mock tool responses."""
    return [
        ToolUseResponseInput(
            tool_name="focused_snippets_searcher",
            tool_use_id="snippets-1",
            response={
                "batch_chunks_search": {
                    "response": [
                        {
                            "chunks": [
                                {
                                    "chunk_id": "chunk1",
                                    "content": "test content",
                                    "file_path": "/test/file.py",
                                    "start_line": 1,
                                    "end_line": 10,
                                }
                            ]
                        }
                    ]
                }
            },
            status=ToolStatus.COMPLETED,
        ),
        ToolUseResponseInput(
            tool_name="iterative_file_reader",
            tool_use_id="reader-1",
            response={
                "data": {
                    "file_path": "/test/file.py",
                    "content": "test file content",
                    "start_line": 1,
                    "end_line": 50,
                }
            },
            status=ToolStatus.COMPLETED,
        ),
        ToolUseResponseInput(
            tool_name="grep_search",
            tool_use_id="grep-1",
            response={
                "matches": [
                    {
                        "file": "/test/file.py",
                        "line": 5,
                        "content": "def test_function():",
                        "context": {"before": [], "after": ["    return True"]},
                    }
                ]
            },
            status=ToolStatus.COMPLETED,
        ),
        ToolUseResponseInput(
            tool_name="ask_user_input",
            tool_use_id="user-input-1",
            response={
                "user_response": "Yes, proceed with the changes",
                "timestamp": "2023-01-01T12:00:00Z",
            },
            status=ToolStatus.COMPLETED,
        ),
    ]


@pytest.fixture
def failed_tool_response():
    """Create a failed tool response for testing error handling."""
    return ToolUseResponseInput(
        tool_name="failing_tool",
        tool_use_id="failed-tool-id",
        response={"error": "Tool execution failed", "code": 500},
        status=ToolStatus.FAILED,
    )


@pytest.fixture
def mock_repository_list():
    """Create a list of mock repositories."""
    return [
        Repository(
            repo_path="/workspace/primary",
            repo_name="primary_repo",
            root_directory_context="primary repo context",
            is_working_repository=True,
        ),
        Repository(
            repo_path="/workspace/secondary",
            repo_name="secondary_repo",
            root_directory_context="secondary repo context",
            is_working_repository=False,
        ),
    ]


@pytest.fixture
def mock_attachment_list():
    """Create a list of mock attachments."""
    return [
        Attachment(
            attachment_id=1,
        ),
        Attachment(
            attachment_id=2,
        ),
        Attachment(
            attachment_id=3,
        ),
    ]


@pytest.fixture
def comprehensive_query_solver_input():
    """Create a comprehensive QuerySolverInput with all possible fields."""
    return QuerySolverInput(
        query="Comprehensive test query with all features enabled",
        write_mode=True,
        session_id=456,
        user_team_id=2,
        session_type="comprehensive_test",
        os_name="windows",
        shell="powershell",
        vscode_env="staging",
        llm_model=LLMModel.GEMINI_2_POINT_5_PRO,
        reasoning="comprehensive",
        search_web=True,
        is_lsp_ready=True,
        is_embedding_done=True,
        deputy_dev_rules="Comprehensive testing rules with detailed guidelines",
        repositories=[
            Repository(
                repo_path="/projects/main",
                repo_name="main_project",
                root_directory_context="main project context with comprehensive features",
                is_working_repository=True,
            )
        ],
        attachments=[
            Attachment(
                attachment_id=1,
            )
        ],
        focus_items=[
            ClassFocusItem(
                type=FocusItemTypes.CLASS,
                path="/src/main.py",
                value="MainClass",
                chunks=[],
            )
        ],
    )
