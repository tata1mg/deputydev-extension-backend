"""
Fixtures for testing BaseCommenterAgent.

This module provides comprehensive fixtures for testing various scenarios
of the BaseCommenterAgent class including different input combinations,
mock data, and edge cases.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationTool,
    LLMCallResponseTypes,
    NonStreamingParsedLLMCallResponse,
    UserAndSystemMessages,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
)
from app.main.blueprints.deputy_dev.models.dto.review_agent_chats_dto import (
    ActorType,
    MessageType,
    ReviewAgentChatDTO,
    TextMessageData,
    ToolStatus,
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
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)


# Mock context service fixtures
@pytest.fixture
def mock_context_service() -> MagicMock:
    """Create a mock IDE review context service."""
    context_service = MagicMock(spec=IdeReviewContextService)
    context_service.get_pr_diff = AsyncMock()
    context_service.review_id = 123
    return context_service


# Mock LLM handler fixtures
@pytest.fixture
def mock_llm_handler() -> MagicMock:
    """Create a mock LLM handler."""
    handler = MagicMock()
    handler.prompt_handler_map = MagicMock()
    handler.start_llm_query = AsyncMock()
    return handler


# Mock prompt handler fixtures
@pytest.fixture
def mock_prompt_handler() -> MagicMock:
    """Create a mock prompt handler."""
    handler = MagicMock()
    handler.get_prompt.return_value = UserAndSystemMessages(
        system_message="Test system message", user_message="Test user message", cached_message="Test cached message"
    )
    handler.disable_tools = False
    return handler


@pytest.fixture
def mock_prompt_handler_tools_enabled() -> MagicMock:
    """Create a mock prompt handler with tools enabled."""
    handler = MagicMock()
    handler.disable_tools = False
    return handler


@pytest.fixture
def mock_prompt_handler_tools_disabled() -> MagicMock:
    """Create a mock prompt handler with tools disabled."""
    handler = MagicMock()
    handler.disable_tools = True
    return handler


# UserAgentDTO fixtures
@pytest.fixture
def sample_user_agent_dto() -> UserAgentDTO:
    """Create a sample UserAgentDTO."""
    return UserAgentDTO(
        id=1,
        agent_name="test_security_agent",
        user_team_id=1,
        display_name="Test Security Agent",
        custom_prompt="Test custom prompt",
        exclusions=[],
        inclusions=[],
        confidence_score=0.85,
        objective="Test agent objective",
        is_custom_agent=False,
        is_deleted=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def user_agent_dto_no_display_name() -> UserAgentDTO:
    """Create a UserAgentDTO without display name."""
    return UserAgentDTO(
        id=2,
        agent_name="test_agent_no_display",
        user_team_id=1,
        display_name=None,  # This should fallback to agent_type.value
        custom_prompt="Test prompt",
        exclusions=[],
        inclusions=[],
        confidence_score=0.8,
        objective="Test objective",
        is_custom_agent=False,
        is_deleted=False,
    )


@pytest.fixture
def user_agent_dto_minimal() -> UserAgentDTO:
    """Create a minimal UserAgentDTO with None values."""
    return UserAgentDTO(
        id=3,
        agent_name="minimal_agent",
        user_team_id=1,
        display_name="Minimal Agent",
        custom_prompt=None,
        exclusions=[],
        inclusions=[],
        confidence_score=0.9,
        objective=None,
        is_custom_agent=False,
        is_deleted=False,
    )


# Relevant chunks fixtures
@pytest.fixture
def sample_relevant_chunks() -> Dict[str, Any]:
    """Create sample relevant chunks data."""
    chunk1 = ChunkInfo(
        content="def test_function():\n    pass",
        file_path="/test/file1.py",
        start_line=1,
        end_line=2,
        chunk_id="chunk_1",
        source_details={"file_path": "/test/file1.py", "start_line": 1, "end_line": 2},
    )
    chunk2 = ChunkInfo(
        content="class TestClass:\n    pass",
        file_path="/test/file2.py",
        start_line=1,
        end_line=2,
        chunk_id="chunk_2",
        source_details={"file_path": "/test/file2.py", "start_line": 1, "end_line": 2},
    )

    return {
        "relevant_chunks": [chunk1, chunk2],
        "relevant_chunks_mapping": {
            1: [0, 1]  # agent_id 1 maps to chunk indices 0 and 1
        },
    }


@pytest.fixture
def empty_relevant_chunks() -> Dict[str, Any]:
    """Create empty relevant chunks data."""
    return {
        "relevant_chunks": [],
        "relevant_chunks_mapping": {
            1: []  # agent_id 1 maps to empty list
        },
    }


# LLM response fixtures
@pytest.fixture
def sample_llm_response() -> NonStreamingParsedLLMCallResponse:
    """Create a sample LLM response."""
    return NonStreamingParsedLLMCallResponse(
        type=LLMCallResponseTypes.NON_STREAMING,
        parsed_content=["Test response content"],
        content=[],
        usage={"input": 100, "output": 50},
        prompt_vars={},
        prompt_id="test_prompt",
        model_used=LLModels.GPT_4O.value,
        query_id=123,
    )


@pytest.fixture
def sample_llm_response_final() -> NonStreamingParsedLLMCallResponse:
    """Create a sample LLM response with final response tool use."""
    mock_content_block = MagicMock()
    mock_content_block.type = ContentBlockCategory.TOOL_USE_REQUEST
    mock_content_block.content = MagicMock()
    mock_content_block.content.tool_name = "parse_final_response"
    mock_content_block.content.tool_use_id = "final_response_123"
    mock_content_block.content.tool_input = {"comments": []}

    return NonStreamingParsedLLMCallResponse(
        type=LLMCallResponseTypes.NON_STREAMING,
        parsed_content=[mock_content_block],
        content=[],
        usage={"input": 150, "output": 75},
        prompt_vars={},
        prompt_id="test_prompt_final",
        model_used=LLModels.GPT_4O.value,
        query_id=124,
    )


@pytest.fixture
def invalid_llm_response() -> MagicMock:
    """Create an invalid LLM response (not NonStreamingParsedLLMCallResponse)."""
    return MagicMock(spec_set=["some_other_field"])


# ReviewAgentChatDTO fixtures
@pytest.fixture
def sample_review_agent_chat_text() -> List[ReviewAgentChatDTO]:
    """Create sample review agent chat with text message."""
    chat = ReviewAgentChatDTO(
        id=1,
        session_id=123,
        agent_id="1",
        actor=ActorType.REVIEW_AGENT,
        message_type=MessageType.TEXT,
        message_data=TextMessageData(text="Sample text message"),
        metadata={"cache_breakpoint": True},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return [chat]


@pytest.fixture
def sample_review_agent_chat_tool() -> List[ReviewAgentChatDTO]:
    """Create sample review agent chat with tool message."""
    chat = ReviewAgentChatDTO(
        id=2,
        session_id=123,
        agent_id="1",
        actor=ActorType.ASSISTANT,
        message_type=MessageType.TOOL_USE,
        message_data=ToolUseMessageData(
            tool_use_id="tool_123",
            tool_name="test_tool",
            tool_input={"param": "value"},
            tool_response={"result": "success"},
            tool_status=ToolStatus.COMPLETED,
        ),
        metadata={},
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return [chat]


# Payload fixtures
@pytest.fixture
def query_payload() -> Dict[str, Any]:
    """Create a query payload."""
    return {"type": "query", "message": "Review this code for security issues"}


@pytest.fixture
def tool_use_response_payload() -> Dict[str, Any]:
    """Create a tool use response payload."""
    return {
        "type": "tool_use_response",
        "tool_use_response": {
            "tool_name": "iterative_file_reader",  # Use a simpler tool
            "tool_use_id": "test_tool_use_id",
            "response": {
                "data": {
                    "chunk": {
                        "content": "file content",
                        "file_path": "/test/file.py",
                        "source_details": {"file_path": "/test/file.py", "start_line": 1, "end_line": 10},
                    },
                    "eof_reached": True,
                    "was_summary": False,
                    "total_lines": 10,
                }
            },
        },
    }


@pytest.fixture
def tool_use_failed_payload() -> Dict[str, Any]:
    """Create a tool use failed payload."""
    return {
        "type": "tool_use_failed",
        "tool_use_response": {
            "tool_name": "iterative_file_reader",
            "tool_use_id": "test_tool_use_id",
            "error_type": "TimeoutError",
            "error_message": "Tool execution timed out",
        },
        "tool_use_failed": True,
    }


@pytest.fixture
def invalid_payload() -> Dict[str, Any]:
    """Create an invalid payload."""
    return {"type": "invalid_type", "message": "This should cause an error"}


# Tool request fixtures
@pytest.fixture
def sample_tool_request() -> Dict[str, Any]:
    """Create a sample tool request."""
    return {
        "tool_name": "grep_search",
        "tool_use_id": "search_123",
        "tool_input": {"query": "security vulnerability", "path": "/src"},
    }


# Final response fixtures
@pytest.fixture
def sample_final_response() -> Dict[str, Any]:
    """Create a sample final response."""
    return {"status": "completed", "comments": []}


@pytest.fixture
def sample_final_response_with_comments() -> Dict[str, Any]:
    """Create a sample final response with comments."""
    comment1 = MagicMock()
    comment1.title = "Security Issue 1"
    comment1.comment = "Found potential security vulnerability"
    comment1.confidence_score = 0.9
    comment1.rationale = "This code pattern is vulnerable"
    comment1.corrective_code = "Use secure coding practices"
    comment1.file_path = "/src/test.py"
    comment1.line_number = 15
    comment1.tag = "security"
    comment1.buckets = None

    comment2 = MagicMock()
    comment2.title = "Security Issue 2"
    comment2.comment = "Another security concern"
    comment2.confidence_score = 0.8
    comment2.rationale = "This could lead to data exposure"
    comment2.corrective_code = "Add validation"
    comment2.file_path = "/src/utils.py"
    comment2.line_number = 25
    comment2.tag = "security"
    comment2.buckets = None

    return {"status": "completed", "comments": [comment1, comment2]}


# Session ID fixtures
@pytest.fixture
def valid_session_id() -> int:
    """Valid session ID for testing."""
    return 12345


@pytest.fixture
def zero_session_id() -> int:
    """Zero session ID for edge case testing."""
    return 0


@pytest.fixture
def invalid_session_id() -> int:
    """Invalid session ID for testing."""
    return -1


# Test agent type scenarios
@pytest.fixture
def all_agent_types() -> List[AgentTypes]:
    """Get all available agent types for comprehensive testing."""
    return list(AgentTypes)


@pytest.fixture
def all_prompt_features() -> List[PromptFeatures]:
    """Get all available prompt features for comprehensive testing."""
    return list(PromptFeatures)


@pytest.fixture
def all_llm_models() -> List[LLModels]:
    """Get all available LLM models for comprehensive testing."""
    return list(LLModels)


# Agent run result fixtures
@pytest.fixture
def sample_agent_run_result_success() -> AgentRunResult:
    """Create a successful agent run result."""
    return AgentRunResult(
        agent_result={"status": "success", "message": "Review completed"},
        prompt_tokens_exceeded=False,
        agent_name="test_security_agent",
        agent_type=AgentTypes.SECURITY,
        model=LLModels.GPT_4O,
        tokens_data={
            "test_security_agent_QUERY": {
                "system_prompt": 100,
                "user_prompt": 50,
                "input_tokens": 150,
                "output_tokens": 75,
            }
        },
        display_name="Test Security Agent",
    )


@pytest.fixture
def sample_agent_run_result_token_exceeded() -> AgentRunResult:
    """Create an agent run result with token limit exceeded."""
    return AgentRunResult(
        agent_result=None,
        prompt_tokens_exceeded=True,
        agent_name="test_security_agent",
        agent_type=AgentTypes.SECURITY,
        model=LLModels.GPT_4O,
        tokens_data={"test_security_agent_QUERY": {"system_prompt": 50000, "user_prompt": 50000}},
        display_name="Test Security Agent",
    )


# Configuration fixtures
@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create mock configuration for testing."""
    return {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 128000}, "GPT_40_MINI": {"INPUT_TOKENS_LIMIT": 64000}}}


@pytest.fixture
def mock_config_low_token_limit() -> Dict[str, Any]:
    """Create mock configuration with low token limits for testing."""
    return {"LLM_MODELS": {"GPT_4O": {"INPUT_TOKENS_LIMIT": 100}, "GPT_40_MINI": {"INPUT_TOKENS_LIMIT": 50}}}


# Tool fixtures
@pytest.fixture
def sample_conversation_tools() -> List[ConversationTool]:
    """Create sample conversation tools."""
    tool1 = MagicMock(spec=ConversationTool)
    tool1.name = "grep_search"

    tool2 = MagicMock(spec=ConversationTool)
    tool2.name = "iterative_file_reader"

    return [tool1, tool2]


# Error scenarios fixtures
@pytest.fixture
def llm_handler_with_exception() -> MagicMock:
    """Create an LLM handler that raises exceptions."""
    handler = MagicMock()
    handler.prompt_handler_map = MagicMock()
    handler.start_llm_query = AsyncMock(side_effect=Exception("LLM query failed"))
    return handler


@pytest.fixture
def context_service_with_exception() -> MagicMock:
    """Create a context service that raises exceptions."""
    service = MagicMock(spec=IdeReviewContextService)
    service.get_pr_diff = AsyncMock(side_effect=Exception("Context service failed"))
    service.review_id = 123
    return service


# UserAndSystemMessages fixtures
@pytest.fixture
def sample_user_and_system_messages() -> UserAndSystemMessages:
    """Create sample user and system messages."""
    return UserAndSystemMessages(
        system_message="You are a helpful code review assistant.",
        user_message="Please review this code for security vulnerabilities.",
        cached_message="Cached system prompt",
    )


@pytest.fixture
def large_user_and_system_messages() -> UserAndSystemMessages:
    """Create large user and system messages for token limit testing."""
    large_content = "x" * 100000  # 100k characters
    return UserAndSystemMessages(
        system_message=f"System: {large_content}",
        user_message=f"User: {large_content}",
        cached_message=f"Cached: {large_content}",
    )


@pytest.fixture
def empty_user_and_system_messages() -> UserAndSystemMessages:
    """Create empty user and system messages."""
    return UserAndSystemMessages(system_message="", user_message="", cached_message="")


# Performance testing fixtures
@pytest.fixture
def large_tokens_data() -> Dict[str, Dict[str, Any]]:
    """Create large tokens data for performance testing."""
    return {
        f"agent_query_{i}": {
            "system_prompt": 1000 + i,
            "user_prompt": 500 + i,
            "input_tokens": 1500 + i,
            "output_tokens": 750 + i,
        }
        for i in range(100)
    }


# Edge case fixtures for prompt variables
@pytest.fixture
def empty_prompt_variables() -> Dict[str, Optional[str]]:
    """Create empty prompt variables."""
    return {}


@pytest.fixture
def sample_prompt_variables() -> Dict[str, Optional[str]]:
    """Create sample prompt variables."""
    return {
        "PULL_REQUEST_DIFF": "diff content with line numbers",
        "PR_DIFF_WITHOUT_LINE_NUMBER": "diff content without line numbers",
        "AGENT_OBJECTIVE": "Review code for security issues",
        "CUSTOM_PROMPT": "Focus on authentication vulnerabilities",
        "AGENT_NAME": "security",
    }


@pytest.fixture
def prompt_variables_with_none_values() -> Dict[str, Optional[str]]:
    """Create prompt variables with None values."""
    return {
        "PULL_REQUEST_DIFF": "diff content",
        "PR_DIFF_WITHOUT_LINE_NUMBER": "diff content",
        "AGENT_OBJECTIVE": None,
        "CUSTOM_PROMPT": None,
        "AGENT_NAME": "security",
    }
