"""
Fixtures for testing InlineEditGenerator.

This module provides comprehensive fixtures for testing various scenarios
of the InlineEditGenerator class including different input combinations,
mock data, and edge cases.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse
from deputydev_core.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails

from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.constants.tools import ToolStatus
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    CodeBlockData,
    MessageType,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    CodeSelectionInput,
    CodeSnippetFocusItem,
    InlineEditInput,
    LLMModel,
    ToolUseResponseInput,
)


@pytest.fixture
def inline_edit_generator() -> Any:
    """Create an InlineEditGenerator instance for testing."""
    # Import here to avoid module-level import issues
    from app.main.blueprints.one_dev.services.query_solver.inline_editor import InlineEditGenerator

    return InlineEditGenerator()


@pytest.fixture
def mock_client_data() -> ClientData:
    """Create mock client data."""
    from deputydev_core.utils.constants.enums import Clients

    return ClientData(
        client=Clients.BACKEND,
        client_version="1.0.0",
    )


@pytest.fixture
def mock_auth_data() -> AuthData:
    """Create mock auth data."""
    return AuthData(
        user_team_id=123,
        user_id=456,
        api_client="test_client",
        platform="test_platform",
    )


@pytest.fixture
def basic_code_selection() -> CodeSelectionInput:
    """Create a basic code selection input."""
    return CodeSelectionInput(
        selected_text="def hello_world():\n    print('Hello, World!')", file_path="/path/to/test_file.py"
    )


@pytest.fixture
def basic_inline_edit_input(mock_auth_data: AuthData, basic_code_selection: CodeSelectionInput) -> InlineEditInput:
    """Create a basic InlineEditInput."""
    return InlineEditInput(
        session_id=123,
        query="Add error handling to this function",
        code_selection=basic_code_selection,
        auth_data=mock_auth_data,
        llm_model=LLMModel.CLAUDE_3_POINT_7_SONNET,
        tool_choice="required",
    )


@pytest.fixture
def tool_use_response_input() -> ToolUseResponseInput:
    """Create a ToolUseResponseInput."""
    return ToolUseResponseInput(
        tool_name="replace_in_file",
        tool_use_id="tool_12345",
        response={"success": True, "changes": "Applied diff successfully"},
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def inline_edit_input_with_tool_response(
    mock_auth_data: AuthData, tool_use_response_input: ToolUseResponseInput
) -> InlineEditInput:
    """Create InlineEditInput with tool use response."""
    return InlineEditInput(
        session_id=123,
        tool_use_response=tool_use_response_input,
        auth_data=mock_auth_data,
        llm_model=LLMModel.CLAUDE_3_POINT_7_SONNET,
        tool_choice="required",
    )


@pytest.fixture
def mock_agent_chat_user(basic_code_selection: CodeSelectionInput) -> AgentChatDTO:
    """Create a mock user agent chat."""
    chunk = ChunkInfo(
        content=basic_code_selection.selected_text,
        source_details=ChunkSourceDetails(
            file_path=basic_code_selection.file_path,
            start_line=1,
            end_line=2,
        ),
    )
    focus_item = CodeSnippetFocusItem(
        chunks=[chunk],
        path=basic_code_selection.file_path,
        value="test_file.py",
    )

    return AgentChatDTO(
        id=1,
        session_id=123,
        actor=ActorType.USER,
        message_type=MessageType.TEXT,
        message_data=TextMessageData(
            text="Add error handling to this function",
            focus_items=[focus_item],
        ),
        query_id="test_query_123",
        metadata={"is_inline_editor": True, "llm_model": "CLAUDE_3_POINT_7_SONNET"},
        previous_queries=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_agent_chat_assistant_code() -> AgentChatDTO:
    """Create a mock assistant agent chat with code block."""
    return AgentChatDTO(
        id=2,
        session_id=123,
        actor=ActorType.ASSISTANT,
        message_type=MessageType.CODE_BLOCK,
        message_data=CodeBlockData(
            code="def hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')",
            language="python",
            file_path="/path/to/test_file.py",
        ),
        query_id="test_query_123",
        metadata={"is_inline_editor": True, "llm_model": "CLAUDE_3_POINT_7_SONNET"},
        previous_queries=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_agent_chat_assistant_tool() -> AgentChatDTO:
    """Create a mock assistant agent chat with tool use."""
    return AgentChatDTO(
        id=3,
        session_id=123,
        actor=ActorType.ASSISTANT,
        message_type=MessageType.TOOL_USE,
        message_data=ToolUseMessageData(
            tool_name="replace_in_file",
            tool_use_id="tool_12345",
            tool_input={
                "path": "/path/to/test_file.py",
                "diff": "------- SEARCH\ndef hello_world():\n    print('Hello, World!')\n=======\ndef hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')\n+++++++ REPLACE",
            },
            tool_response=None,
        ),
        query_id="test_query_123",
        metadata={"is_inline_editor": True, "llm_model": "CLAUDE_3_POINT_7_SONNET"},
        previous_queries=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_agent_chat_assistant_tool_with_response() -> AgentChatDTO:
    """Create a mock assistant agent chat with tool use and response."""
    return AgentChatDTO(
        id=3,
        session_id=123,
        actor=ActorType.ASSISTANT,
        message_type=MessageType.TOOL_USE,
        message_data=ToolUseMessageData(
            tool_name="replace_in_file",
            tool_use_id="tool_12345",
            tool_input={
                "path": "/path/to/test_file.py",
                "diff": "------- SEARCH\ndef hello_world():\n    print('Hello, World!')\n=======\ndef hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')\n+++++++ REPLACE",
            },
            tool_response={"success": True, "changes": "Applied diff successfully"},
        ),
        query_id="test_query_123",
        metadata={"is_inline_editor": True, "llm_model": "CLAUDE_3_POINT_7_SONNET"},
        previous_queries=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_llm_response_with_code() -> Any:
    """Create a mock LLM response with code snippets."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [
        {
            "code_snippets": [
                {
                    "code": "def hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')",
                    "programming_language": "python",
                    "file_path": "/path/to/test_file.py",
                }
            ]
        }
    ]
    return response


@pytest.fixture
def mock_llm_response_with_tool_use() -> Any:
    """Create a mock LLM response with tool use request."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [
        {
            "type": "TOOL_USE_REQUEST",
            "content": {
                "tool_name": "replace_in_file",
                "tool_use_id": "tool_12345",
                "tool_input": {
                    "path": "/path/to/test_file.py",
                    "diff": "------- SEARCH\ndef hello_world():\n    print('Hello, World!')\n=======\ndef hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')\n+++++++ REPLACE",
                },
            },
        }
    ]
    return response


@pytest.fixture
def mock_llm_response_mixed() -> Any:
    """Create a mock LLM response with both code snippets and tool use."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [
        {
            "code_snippets": [
                {
                    "code": "def hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')",
                    "programming_language": "python",
                    "file_path": "/path/to/test_file.py",
                }
            ]
        },
        {
            "type": "TOOL_USE_REQUEST",
            "content": {
                "tool_name": "replace_in_file",
                "tool_use_id": "tool_67890",
                "tool_input": {
                    "path": "/path/to/test_file.py",
                    "diff": "------- SEARCH\ndef hello_world():\n    print('Hello, World!')\n=======\ndef hello_world():\n    try:\n        print('Hello, World!')\n    except Exception as e:\n        print(f'Error: {e}')\n+++++++ REPLACE",
                },
            },
        },
    ]
    return response


@pytest.fixture
def mock_job_dto() -> JobDTO:
    """Create a mock JobDTO."""
    return JobDTO(
        id=123,
        type="INLINE_EDIT",
        session_id="123",
        user_team_id=123,
        status="PENDING",
        final_output=None,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_llm_handler() -> MagicMock:
    """Create a mock LLM handler."""
    mock_handler = MagicMock()
    mock_handler.start_llm_query = AsyncMock()
    return mock_handler


@pytest.fixture
def mock_agent_chats_repository() -> MagicMock:
    """Create a mock AgentChatsRepository."""
    mock_repo = MagicMock()
    mock_repo.create_chat = AsyncMock()
    mock_repo.update_chat = AsyncMock()
    mock_repo.get_chats_by_session_id = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_job_service() -> MagicMock:
    """Create a mock JobService."""
    mock_service = MagicMock()
    mock_service.db_create = AsyncMock()
    mock_service.db_update = AsyncMock()
    return mock_service


@pytest.fixture
def mock_prompt_feature_factory() -> MagicMock:
    """Create a mock PromptFeatureFactory."""
    mock_factory = MagicMock()
    mock_prompt_handler = MagicMock()
    mock_prompt_handler.get_prompt.return_value.user_message = "Generate improved code with error handling"
    mock_factory.get_prompt.return_value = mock_prompt_handler
    return mock_factory


@pytest.fixture
def invalid_inline_edit_input(mock_auth_data: AuthData) -> InlineEditInput:
    """Create an invalid InlineEditInput (missing both query+code_selection and tool_use_response)."""
    return InlineEditInput(
        session_id=123,
        auth_data=mock_auth_data,
        llm_model=LLMModel.CLAUDE_3_POINT_7_SONNET,
    )


@pytest.fixture
def gpt_4_inline_edit_input(mock_auth_data: AuthData, basic_code_selection: CodeSelectionInput) -> InlineEditInput:
    """Create InlineEditInput with GPT-4 model."""
    return InlineEditInput(
        session_id=123,
        query="Add error handling to this function",
        code_selection=basic_code_selection,
        auth_data=mock_auth_data,
        llm_model=LLMModel.GPT_4_POINT_1,
        tool_choice="required",
    )


@pytest.fixture
def empty_llm_response() -> Any:
    """Create an empty LLM response."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = []
    return response
