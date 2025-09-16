"""
Fixtures for testing remaining QuerySolver methods.

This module provides comprehensive fixtures for testing various scenarios
of the remaining QuerySolver methods that don't have test coverage yet.
"""

from datetime import datetime
from typing import List
from unittest.mock import MagicMock

import pytest

from app.backend_common.models.dto.extension_sessions_dto import ExtensionSessionData
from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    MessageThreadDTO,
    MessageType,
    TextBlockContent,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.main.blueprints.one_dev.constants.tools import ToolStatus
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    CodeBlockData,
    TextMessageData,
    ThinkingInfoData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.models.dto.query_solver_agents_dto import QuerySolverAgentsDTO
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.query_solver.agents.custom_query_solver_agent import (
    CustomQuerySolverAgent,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    FocusItem,
    RetryReasons,
    ToolUseResponseInput,
)


@pytest.fixture
def mock_extension_session_data() -> ExtensionSessionData:
    """Create mock extension session data."""
    return ExtensionSessionData(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        current_model=LLModels.GPT_4_POINT_1,
        summary="Test session summary",
    )


@pytest.fixture
def mock_existing_extension_session() -> ExtensionSessionData:
    """Create mock existing extension session with summary."""
    return ExtensionSessionData(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        current_model=LLModels.GPT_4_POINT_1,
        summary="Existing session summary",
    )


@pytest.fixture
def mock_extension_session_without_summary() -> ExtensionSessionData:
    """Create mock extension session without summary."""
    return ExtensionSessionData(
        session_id=123,
        user_team_id=1,
        session_type="test_session",
        current_model=LLModels.GPT_4_POINT_1,
        summary=None,
    )


@pytest.fixture
def mock_query_summary_data() -> QuerySummaryData:
    """Create mock query summary data."""
    return QuerySummaryData(
        session_id=123,
        query_id="test-query-id",
        summary="Test query summary",
    )


@pytest.fixture
def mock_existing_query_summary() -> QuerySummaryData:
    """Create mock existing query summary."""
    return QuerySummaryData(
        session_id=123,
        query_id="test-query-id",
        summary="Existing query summary",
    )


@pytest.fixture
def mock_query_solver_agent_dto() -> QuerySolverAgentsDTO:
    """Create mock query solver agent DTO."""
    return QuerySolverAgentsDTO(
        id=1,
        name="test_agent",
        agent_enum="TEST_AGENT",
        description="Test agent description",
        allowed_first_party_tools=["file_reader", "code_searcher"],
        prompt_intent="Test prompt intent for the agent",
        status="ACTIVE",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_multiple_query_solver_agents() -> List[QuerySolverAgentsDTO]:
    """Create multiple mock query solver agent DTOs."""
    return [
        QuerySolverAgentsDTO(
            id=1,
            name="file_manager_agent",
            agent_enum="FILE_MANAGER_AGENT",
            description="Agent for file management tasks",
            allowed_first_party_tools=["file_reader", "write_to_file"],
            prompt_intent="Handle file operations and management",
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        QuerySolverAgentsDTO(
            id=2,
            name="code_analyzer_agent",
            agent_enum="CODE_ANALYZER_AGENT",
            description="Agent for code analysis tasks",
            allowed_first_party_tools=["focused_snippets_searcher", "grep_search"],
            prompt_intent="Analyze and search through code",
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        QuerySolverAgentsDTO(
            id=3,
            name="terminal_agent",
            agent_enum="TERMINAL_AGENT",
            description="Agent for terminal operations",
            allowed_first_party_tools=["execute_command"],
            prompt_intent="Execute terminal and system commands",
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def mock_message_thread_dto() -> MessageThreadDTO:
    """Create mock message thread DTO."""
    from app.backend_common.models.dto.message_thread_dto import MessageThreadActor

    return MessageThreadDTO(
        id=1,
        session_id=123,
        actor=MessageThreadActor.USER,
        message_type=MessageType.QUERY,
        data_hash="test_hash",
        message_data=[TextBlockData(content=TextBlockContent(text="test query"))],
        prompt_type="CODE_QUERY_SOLVER",
        prompt_category="query_solver",
        llm_model=LLModels.GPT_4_POINT_1,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_multiple_message_threads() -> List[MessageThreadDTO]:
    """Create multiple mock message thread DTOs."""
    from app.backend_common.models.dto.message_thread_dto import MessageThreadActor, TextBlockContent, TextBlockData

    return [
        MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.ASSISTANT,
            message_type=MessageType.RESPONSE,
            data_hash="hash1",
            message_data=[TextBlockData(content=TextBlockContent(text="response"))],
            prompt_type="OTHER",
            prompt_category="other",
            llm_model=LLModels.GPT_4_POINT_1,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.fromisoformat("2023-01-01T10:00:00"),
            updated_at=datetime.fromisoformat("2023-01-01T10:00:00"),
        ),
        MessageThreadDTO(
            id=2,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.QUERY,
            data_hash="hash2",
            message_data=[TextBlockData(content=TextBlockContent(text="first query"))],
            prompt_type="CODE_QUERY_SOLVER",
            prompt_category="query_solver",
            llm_model=LLModels.GPT_4_POINT_1,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.fromisoformat("2023-01-01T11:00:00"),
            updated_at=datetime.fromisoformat("2023-01-01T11:00:00"),
        ),
        MessageThreadDTO(
            id=3,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.QUERY,
            data_hash="hash3",
            message_data=[TextBlockData(content=TextBlockContent(text="second query"))],
            prompt_type="CUSTOM_CODE_QUERY_SOLVER",
            prompt_category="query_solver",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.fromisoformat("2023-01-01T12:00:00"),
            updated_at=datetime.fromisoformat("2023-01-01T12:00:00"),
        ),
    ]


@pytest.fixture
def mock_agent_chat_list_for_summary() -> List[AgentChatDTO]:
    """Create mock agent chat list for summary generation."""
    return [
        AgentChatDTO(
            id=1,
            session_id=123,
            actor=ActorType.USER,
            message_data=TextMessageData(text="How do I create a new file?"),
            message_type=ChatMessageType.TEXT,
            metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
            query_id="test-query-id",
            previous_queries=[],
            created_at=datetime.fromisoformat("2023-01-01T10:00:00"),
            updated_at=datetime.fromisoformat("2023-01-01T10:00:00"),
        ),
        AgentChatDTO(
            id=2,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=TextMessageData(
                text="I'll help you create a new file. Let me check the current directory structure."
            ),
            message_type=ChatMessageType.TEXT,
            metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
            query_id="test-query-id",
            previous_queries=[],
            created_at=datetime.fromisoformat("2023-01-01T10:01:00"),
            updated_at=datetime.fromisoformat("2023-01-01T10:01:00"),
        ),
        AgentChatDTO(
            id=3,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=ToolUseMessageData(
                tool_use_id="tool-1",
                tool_name="file_path_searcher",
                tool_input={"directory": ".", "search_terms": []},
                tool_response={"files": ["main.py", "utils.py"]},
            ),
            message_type=ChatMessageType.TOOL_USE,
            metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
            query_id="test-query-id",
            previous_queries=[],
            created_at=datetime.fromisoformat("2023-01-01T10:02:00"),
            updated_at=datetime.fromisoformat("2023-01-01T10:02:00"),
        ),
        AgentChatDTO(
            id=4,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=CodeBlockData(
                language="python",
                file_path="/new_file.py",
                code="# New Python file\nprint('Hello, World!')",
                diff="# New Python file\nprint('Hello, World!')",
            ),
            message_type=ChatMessageType.CODE_BLOCK,
            metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
            query_id="test-query-id",
            previous_queries=[],
            created_at=datetime.fromisoformat("2023-01-01T10:03:00"),
            updated_at=datetime.fromisoformat("2023-01-01T10:03:00"),
        ),
    ]


@pytest.fixture
def mock_tool_use_agent_chat() -> AgentChatDTO:
    """Create mock agent chat with tool use for updating."""
    return AgentChatDTO(
        id=1,
        session_id=123,
        actor=ActorType.ASSISTANT,
        message_data=ToolUseMessageData(
            tool_use_id="test-tool-use-id",
            tool_name="test_tool",
            tool_input={"param": "value"},
            tool_response=None,
        ),
        message_type=ChatMessageType.TOOL_USE,
        metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
        query_id="test-query-id",
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_tool_use_response_input() -> ToolUseResponseInput:
    """Create mock tool use response input."""
    return ToolUseResponseInput(
        tool_name="test_tool",
        tool_use_id="test-tool-use-id",
        response={"result": "success", "data": "test_data"},
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def mock_failed_tool_use_response_input() -> ToolUseResponseInput:
    """Create mock failed tool use response input."""
    return ToolUseResponseInput(
        tool_name="failing_tool",
        tool_use_id="failing-tool-use-id",
        response={"error": "Tool execution failed", "code": 500},
        status=ToolStatus.FAILED,
    )


@pytest.fixture
def mock_complex_agent_chat_list() -> List[AgentChatDTO]:
    """Create complex mock agent chat list with different message types."""
    return [
        AgentChatDTO(
            id=1,
            session_id=123,
            actor=ActorType.USER,
            message_data=TextMessageData(text="Can you help me refactor this code?"),
            message_type=ChatMessageType.TEXT,
            metadata={"llm_model": "gpt-4", "agent_name": "code_refactor_agent"},
            query_id="refactor-query-id",
            previous_queries=["previous-query-1"],
            created_at=datetime.fromisoformat("2023-01-01T14:00:00"),
            updated_at=datetime.fromisoformat("2023-01-01T14:00:00"),
        ),
        AgentChatDTO(
            id=2,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=ThinkingInfoData(
                thinking_summary="I need to analyze the code structure first...",
                ignore_in_chat=False,
            ),
            message_type=ChatMessageType.THINKING,
            metadata={"llm_model": "gpt-4", "agent_name": "code_refactor_agent"},
            query_id="refactor-query-id",
            previous_queries=["previous-query-1"],
            created_at=datetime.fromisoformat("2023-01-01T14:01:00"),
            updated_at=datetime.fromisoformat("2023-01-01T14:01:00"),
        ),
        AgentChatDTO(
            id=3,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=ToolUseMessageData(
                tool_use_id="refactor-tool-1",
                tool_name="focused_snippets_searcher",
                tool_input={"search_terms": ["class", "function"]},
                tool_response={
                    "chunks": [
                        {
                            "chunk_id": "chunk1",
                            "content": "class OldClass:\n    def old_method(self):\n        pass",
                            "file_path": "/src/old_code.py",
                        }
                    ]
                },
            ),
            message_type=ChatMessageType.TOOL_USE,
            metadata={"llm_model": "gpt-4", "agent_name": "code_refactor_agent"},
            query_id="refactor-query-id",
            previous_queries=["previous-query-1"],
            created_at=datetime.fromisoformat("2023-01-01T14:02:00"),
            updated_at=datetime.fromisoformat("2023-01-01T14:02:00"),
        ),
        AgentChatDTO(
            id=4,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=TextMessageData(text="I've analyzed your code. Here's the refactored version:"),
            message_type=ChatMessageType.TEXT,
            metadata={"llm_model": "gpt-4", "agent_name": "code_refactor_agent"},
            query_id="refactor-query-id",
            previous_queries=["previous-query-1"],
            created_at=datetime.fromisoformat("2023-01-01T14:03:00"),
            updated_at=datetime.fromisoformat("2023-01-01T14:03:00"),
        ),
        AgentChatDTO(
            id=5,
            session_id=123,
            actor=ActorType.ASSISTANT,
            message_data=CodeBlockData(
                language="python",
                file_path="/src/refactored_code.py",
                code="class RefactoredClass:\n    def improved_method(self):\n        return 'improved'",
                diff="class RefactoredClass:\n    def improved_method(self):\n        return 'improved'",
            ),
            message_type=ChatMessageType.CODE_BLOCK,
            metadata={"llm_model": "gpt-4", "agent_name": "code_refactor_agent"},
            query_id="refactor-query-id",
            previous_queries=["previous-query-1"],
            created_at=datetime.fromisoformat("2023-01-01T14:04:00"),
            updated_at=datetime.fromisoformat("2023-01-01T14:04:00"),
        ),
    ]


@pytest.fixture
def mock_agent_with_no_tool_response() -> AgentChatDTO:
    """Create mock agent chat with tool use but no response."""
    return AgentChatDTO(
        id=1,
        session_id=123,
        actor=ActorType.ASSISTANT,
        message_data=ToolUseMessageData(
            tool_use_id="no-response-tool-id",
            tool_name="no_response_tool",
            tool_input={"param": "value"},
            tool_response=None,
        ),
        message_type=ChatMessageType.TOOL_USE,
        metadata={"llm_model": "gpt-4", "agent_name": "test_agent"},
        query_id="test-query-id",
        previous_queries=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_session_summary_llm_response() -> NonStreamingParsedLLMCallResponse:
    """Create mock LLM response for session summary generation."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [{"summary": "Generated session summary from LLM"}]
    return response


@pytest.fixture
def mock_query_summary_llm_response() -> NonStreamingParsedLLMCallResponse:
    """Create mock LLM response for query summary generation."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [MagicMock(summary="Generated query summary", success=True)]
    return response


@pytest.fixture
def mock_query_summary_llm_response_without_success() -> NonStreamingParsedLLMCallResponse:
    """Create mock LLM response for query summary generation without success attribute."""
    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    mock_content = MagicMock()
    mock_content.summary = "Generated query summary"
    # Simulate missing success attribute
    del mock_content.success
    response.parsed_content = [mock_content]
    return response


@pytest.fixture
def mock_focus_items() -> List[FocusItem]:
    """Create mock focus items."""
    from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
        FileFocusItem,
        FocusItemTypes,
    )

    return [
        FileFocusItem(
            type=FocusItemTypes.FILE,
            path="/src/main.py",
            value="main.py",
        ),
        FileFocusItem(
            type=FocusItemTypes.FILE,
            path="/src/utils.py",
            value="utils.py",
        ),
    ]


@pytest.fixture
def mock_multiple_custom_agents() -> List[CustomQuerySolverAgent]:
    """Create multiple mock custom query solver agents."""
    return [
        CustomQuerySolverAgent(
            agent_name="file_manager_agent",
            agent_description="Agent for file management tasks",
            allowed_tools=["file_reader", "write_to_file"],
            prompt_intent="Handle file operations and management",
        ),
        CustomQuerySolverAgent(
            agent_name="code_analyzer_agent",
            agent_description="Agent for code analysis tasks",
            allowed_tools=["focused_snippets_searcher", "grep_search"],
            prompt_intent="Analyze and search through code",
        ),
    ]


@pytest.fixture
def mock_model_change_scenarios():
    """Create scenarios for testing model change text generation."""
    return {
        "tool_use_failed": {
            "current_model": LLModels.GPT_4_POINT_1,
            "new_model": LLModels.CLAUDE_3_POINT_5_SONNET,
            "retry_reason": RetryReasons.TOOL_USE_FAILED,
            "expected_text": "LLM model changed from GPT-4o Mini to Claude 3.5 Sonnet due to tool use failure.",
        },
        "throttled": {
            "current_model": LLModels.CLAUDE_3_POINT_5_SONNET,
            "new_model": LLModels.GEMINI_2_POINT_5_PRO,
            "retry_reason": RetryReasons.THROTTLED,
            "expected_text": "LLM model changed from Claude 3.5 Sonnet to Gemini 2.5 Pro due to throttling.",
        },
        "token_limit_exceeded": {
            "current_model": LLModels.GEMINI_2_POINT_5_PRO,
            "new_model": LLModels.GPT_4_POINT_1,
            "retry_reason": RetryReasons.TOKEN_LIMIT_EXCEEDED,
            "expected_text": "LLM model changed from Gemini 2.5 Pro to GPT-4o Mini due to token limit exceeded.",
        },
        "user_changed": {
            "current_model": LLModels.GPT_4_POINT_1,
            "new_model": LLModels.CLAUDE_3_POINT_5_SONNET,
            "retry_reason": None,
            "expected_text": "LLM model changed from GPT-4o Mini to Claude 3.5 Sonnet by the user.",
        },
    }
