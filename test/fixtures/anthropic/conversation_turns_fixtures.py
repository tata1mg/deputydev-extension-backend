"""
Fixtures for testing Anthropic get_conversation_turns functionality.

This module provides test fixtures for different conversation turn scenarios
including text messages, tool requests/responses, file attachments, and
extended thinking content specific to Anthropic provider.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest

from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO
from app.backend_common.models.dto.message_thread_dto import (
    ExtendedThinkingContent,
    ExtendedThinkingData,
    FileBlockData,
    FileContent,
    LLModels,
    LLMUsage,
    MessageCallChainCategory,
    MessageThreadActor,
    MessageThreadDTO,
    MessageType,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import (
    ChatAttachmentDataWithObjectBytes,
)


@pytest.fixture
def anthropic_simple_text_message() -> MessageThreadDTO:
    """Create a simple text message from user for Anthropic provider."""
    return MessageThreadDTO(
        id=1,
        session_id=123,
        actor=MessageThreadActor.USER,
        query_id=1,
        message_type=MessageType.QUERY,
        conversation_chain=[1],
        data_hash="test_hash_1",
        message_data=[TextBlockData(content=TextBlockContent(text="Hello, how can you help me today?"))],
        prompt_type="user_query",
        prompt_category="general",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_assistant_text_message() -> MessageThreadDTO:
    """Create a simple text response from assistant for Anthropic provider."""
    return MessageThreadDTO(
        id=2,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=1,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2],
        data_hash="test_hash_2",
        message_data=[TextBlockData(content=TextBlockContent(text="I'd be happy to help you with anything you need!"))],
        prompt_type="assistant_response",
        prompt_category="general",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=LLMUsage(input=12, output=18),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_tool_use_request_message() -> MessageThreadDTO:
    """Create a message with tool use request from assistant for Anthropic provider."""
    return MessageThreadDTO(
        id=3,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=2,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2, 3],
        data_hash="test_hash_3",
        message_data=[
            ToolUseRequestData(
                content=ToolUseRequestContent(
                    tool_input={"search_query": "Python code examples"},
                    tool_name="web_search",
                    tool_use_id="call_anthropic_123",
                )
            )
        ],
        prompt_type="assistant_response",
        prompt_category="tool_use",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=LLMUsage(input=25, output=8),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_tool_use_response_message() -> MessageThreadDTO:
    """Create a message with tool use response for Anthropic provider."""
    return MessageThreadDTO(
        id=4,
        session_id=123,
        actor=MessageThreadActor.USER,
        query_id=2,
        message_type=MessageType.TOOL_RESPONSE,
        conversation_chain=[1, 2, 3, 4],
        data_hash="test_hash_4",
        message_data=[
            ToolUseResponseData(
                content=ToolUseResponseContent(
                    tool_name="web_search",
                    tool_use_id="call_anthropic_123",
                    response={"results": ["Example 1: Hello World", "Example 2: Functions", "Example 3: Classes"]},
                )
            )
        ],
        prompt_type="tool_response",
        prompt_category="tool_use",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_message_with_file_attachment() -> MessageThreadDTO:
    """Create a message with file attachment for Anthropic provider."""
    return MessageThreadDTO(
        id=5,
        session_id=123,
        actor=MessageThreadActor.USER,
        query_id=3,
        message_type=MessageType.QUERY,
        conversation_chain=[1, 2, 3, 4, 5],
        data_hash="test_hash_5",
        message_data=[FileBlockData(content=FileContent(attachment_id=50))],
        prompt_type="user_query",
        prompt_category="file_upload",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_message_with_thinking_content() -> MessageThreadDTO:
    """Create a message with thinking content for Anthropic provider."""
    return MessageThreadDTO(
        id=6,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=3,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2, 3, 4, 5, 6],
        data_hash="test_hash_6",
        message_data=[
            ExtendedThinkingData(
                content=ExtendedThinkingContent(
                    type="thinking", thinking="Let me analyze this problem step by step...", signature="claude_thinking"
                )
            )
        ],
        prompt_type="assistant_response",
        prompt_category="thinking",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=LLMUsage(input=8, output=35),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_message_with_redacted_thinking() -> MessageThreadDTO:
    """Create a message with redacted thinking content for Anthropic provider."""
    return MessageThreadDTO(
        id=7,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=4,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2, 3, 4, 5, 6, 7],
        data_hash="test_hash_7",
        message_data=[
            ExtendedThinkingData(
                content=ExtendedThinkingContent(
                    type="redacted_thinking", thinking="This content has been redacted", signature="claude_redacted"
                )
            )
        ],
        prompt_type="assistant_response",
        prompt_category="thinking",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=LLMUsage(input=5, output=20),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_mixed_content_message() -> MessageThreadDTO:
    """Create a message with mixed content types for Anthropic provider."""
    return MessageThreadDTO(
        id=8,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=4,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2, 3, 4, 5, 6, 7, 8],
        data_hash="test_hash_8",
        message_data=[
            TextBlockData(content=TextBlockContent(text="Let me search for that information:")),
            ToolUseRequestData(
                content=ToolUseRequestContent(
                    tool_input={"filename": "/home/user/data.json"},
                    tool_name="read_file_tool",
                    tool_use_id="call_anthropic_456",
                )
            ),
        ],
        prompt_type="assistant_response",
        prompt_category="mixed",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=LLMUsage(input=20, output=12),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_simple_conversation_history(
    anthropic_simple_text_message: MessageThreadDTO,
    anthropic_assistant_text_message: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Create a simple conversation history for Anthropic provider."""
    return [anthropic_simple_text_message, anthropic_assistant_text_message]


@pytest.fixture
def anthropic_complex_conversation_history(
    anthropic_simple_text_message: MessageThreadDTO,
    anthropic_tool_use_request_message: MessageThreadDTO,
    anthropic_tool_use_response_message: MessageThreadDTO,
    anthropic_mixed_content_message: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Create a complex conversation history for Anthropic provider."""
    return [
        anthropic_simple_text_message,
        anthropic_tool_use_request_message,
        anthropic_tool_use_response_message,
        anthropic_mixed_content_message,
    ]


@pytest.fixture
def anthropic_conversation_with_multiple_tool_calls() -> List[MessageThreadDTO]:
    """Create conversation history with multiple tool calls for Anthropic provider."""
    return [
        MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[TextBlockData(content=TextBlockContent(text="Can you analyze both Python and Ruby code?"))],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        MessageThreadDTO(
            id=2,
            session_id=123,
            actor=MessageThreadActor.ASSISTANT,
            query_id=1,
            message_type=MessageType.RESPONSE,
            conversation_chain=[1, 2],
            data_hash="hash_2",
            message_data=[
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"language": "python", "action": "analyze"},
                        tool_name="code_analyzer",
                        tool_use_id="call_py_123",
                    )
                ),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"language": "ruby", "action": "analyze"},
                        tool_name="code_analyzer",
                        tool_use_id="call_rb_456",
                    )
                ),
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        MessageThreadDTO(
            id=3,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1, 2, 3],
            data_hash="hash_3",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="code_analyzer",
                        tool_use_id="call_py_123",
                        response={"analysis": "Python code is well-structured", "score": 85},
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        MessageThreadDTO(
            id=4,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1, 2, 3, 4],
            data_hash="hash_4",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="code_analyzer",
                        tool_use_id="call_rb_456",
                        response={"analysis": "Ruby code follows conventions", "score": 92},
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def anthropic_mock_image_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Create mock image attachment data for Anthropic provider."""
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=50,
            file_name="claude_test_image.jpg",
            file_type="image/jpeg",
            s3_key="test-bucket/claude_test_image.jpg",
            status="uploaded",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        object_bytes=b"fake_jpeg_image_data_for_claude",
    )


@pytest.fixture
def anthropic_mock_document_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Create mock document attachment data for Anthropic provider."""
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=200,
            file_name="claude_test_document.txt",
            file_type="text/plain",
            s3_key="test-bucket/claude_test_document.txt",
            status="uploaded",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        object_bytes=b"fake_text_document_data_for_claude",
    )


@pytest.fixture
def anthropic_attachment_data_task_map_empty() -> Dict[int, asyncio.Task]:
    """Create an empty attachment data task map for Anthropic provider."""
    return {}


@pytest.fixture
def anthropic_attachment_data_task_map_with_image(
    anthropic_mock_image_attachment_data: ChatAttachmentDataWithObjectBytes,
) -> Dict[int, Any]:
    """Create attachment data task map with image for Anthropic provider."""

    async def get_image_data() -> ChatAttachmentDataWithObjectBytes:
        return anthropic_mock_image_attachment_data

    return {50: get_image_data}


@pytest.fixture
def anthropic_attachment_data_task_map_with_document(
    anthropic_mock_document_attachment_data: ChatAttachmentDataWithObjectBytes,
) -> Dict[int, Any]:
    """Create attachment data task map with document for Anthropic provider."""

    async def get_document_data() -> ChatAttachmentDataWithObjectBytes:
        return anthropic_mock_document_attachment_data

    return {200: get_document_data}


@pytest.fixture
def anthropic_out_of_order_tool_conversation() -> List[MessageThreadDTO]:
    """Create conversation where tool responses arrive out of order for Anthropic provider."""
    return [
        # User message
        MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[TextBlockData(content=TextBlockContent(text="Run these analysis tools"))],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # Assistant with multiple tool requests
        MessageThreadDTO(
            id=2,
            session_id=123,
            actor=MessageThreadActor.ASSISTANT,
            query_id=1,
            message_type=MessageType.RESPONSE,
            conversation_chain=[1, 2],
            data_hash="hash_2",
            message_data=[
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"task": "first_analysis"}, tool_name="analyzer_alpha", tool_use_id="call_alpha_111"
                    )
                ),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"task": "second_analysis"}, tool_name="analyzer_beta", tool_use_id="call_beta_222"
                    )
                ),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"task": "third_analysis"}, tool_name="analyzer_gamma", tool_use_id="call_gamma_333"
                    )
                ),
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        # Tool responses in different order
        MessageThreadDTO(
            id=3,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1, 2, 3],
            data_hash="hash_3",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="analyzer_beta", tool_use_id="call_beta_222", response="Second analysis complete"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        MessageThreadDTO(
            id=4,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1, 2, 3, 4],
            data_hash="hash_4",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="analyzer_alpha", tool_use_id="call_alpha_111", response="First analysis complete"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        MessageThreadDTO(
            id=5,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1, 2, 3, 4, 5],
            data_hash="hash_5",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="analyzer_gamma", tool_use_id="call_gamma_333", response="Third analysis complete"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def anthropic_message_with_empty_text() -> MessageThreadDTO:
    """Create a message with empty text content for Anthropic provider."""
    return MessageThreadDTO(
        id=9,
        session_id=123,
        actor=MessageThreadActor.USER,
        query_id=5,
        message_type=MessageType.QUERY,
        conversation_chain=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        data_hash="test_hash_9",
        message_data=[
            TextBlockData(
                content=TextBlockContent(text="   ")  # Just whitespace
            )
        ],
        prompt_type="user_query",
        prompt_category="general",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def anthropic_message_with_multiple_text_blocks() -> MessageThreadDTO:
    """Create a message with multiple text blocks for Anthropic provider."""
    return MessageThreadDTO(
        id=10,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=6,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        data_hash="test_hash_10",
        message_data=[
            TextBlockData(content=TextBlockContent(text="First response part")),
            TextBlockData(content=TextBlockContent(text="Second response part")),
            TextBlockData(content=TextBlockContent(text="Third response part")),
        ],
        prompt_type="assistant_response",
        prompt_category="general",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        usage=LLMUsage(input=15, output=25),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
