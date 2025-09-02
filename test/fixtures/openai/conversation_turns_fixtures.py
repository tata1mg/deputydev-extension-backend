"""
Fixtures for testing OpenAI get_conversation_turns functionality.

This module provides test fixtures for different conversation turn scenarios
including text messages, tool requests/responses, file attachments, and
extended thinking content.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
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
from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO


@pytest.fixture
def simple_text_message() -> MessageThreadDTO:
    """Create a simple text message from user."""
    return MessageThreadDTO(
        id=1,
        session_id=123,
        actor=MessageThreadActor.USER,
        query_id=1,
        message_type=MessageType.QUERY,
        conversation_chain=[1],
        data_hash="test_hash_1",
        message_data=[
            TextBlockData(
                content=TextBlockContent(text="Hello, how are you?")
            )
        ],
        prompt_type="user_query",
        prompt_category="general",
        llm_model=LLModels.GPT_4O,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def assistant_text_message() -> MessageThreadDTO:
    """Create a simple text response from assistant."""
    return MessageThreadDTO(
        id=2,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=1,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2],
        data_hash="test_hash_2",
        message_data=[
            TextBlockData(
                content=TextBlockContent(text="I'm doing well, thank you for asking!")
            )
        ],
        prompt_type="assistant_response",
        prompt_category="general",
        llm_model=LLModels.GPT_4O,
        usage=LLMUsage(input=10, output=15),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def tool_use_request_message() -> MessageThreadDTO:
    """Create a message with tool use request from assistant."""
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
                    tool_input={"query": "Python best practices"},
                    tool_name="search_tool",
                    tool_use_id="tool_123"
                )
            )
        ],
        prompt_type="assistant_response",
        prompt_category="tool_use",
        llm_model=LLModels.GPT_4O,
        usage=LLMUsage(input=20, output=5),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def tool_use_response_message() -> MessageThreadDTO:
    """Create a message with tool use response."""
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
                    tool_name="search_tool",
                    tool_use_id="tool_123",
                    response={"results": ["Follow PEP 8", "Use type hints", "Write tests"]}
                )
            )
        ],
        prompt_type="tool_response",
        prompt_category="tool_use",
        llm_model=LLModels.GPT_4O,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def message_with_file_attachment() -> MessageThreadDTO:
    """Create a message with file attachment."""
    return MessageThreadDTO(
        id=5,
        session_id=123,
        actor=MessageThreadActor.USER,
        query_id=3,
        message_type=MessageType.QUERY,
        conversation_chain=[1, 2, 3, 4, 5],
        data_hash="test_hash_5",
        message_data=[
            FileBlockData(
                content=FileContent(attachment_id=42)
            )
        ],
        prompt_type="user_query",
        prompt_category="file_upload",
        llm_model=LLModels.GPT_4O,
        usage=None,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def message_with_extended_thinking() -> MessageThreadDTO:
    """Create a message with extended thinking content."""
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
                    type="thinking",
                    thinking="Let me think about this carefully...",
                    signature="assistant_thinking"
                )
            )
        ],
        prompt_type="assistant_response",
        prompt_category="thinking",
        llm_model=LLModels.GPT_4O,
        usage=LLMUsage(input=5, output=25),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mixed_content_message() -> MessageThreadDTO:
    """Create a message with mixed content types."""
    return MessageThreadDTO(
        id=7,
        session_id=123,
        actor=MessageThreadActor.ASSISTANT,
        query_id=4,
        message_type=MessageType.RESPONSE,
        conversation_chain=[1, 2, 3, 4, 5, 6, 7],
        data_hash="test_hash_7",
        message_data=[
            TextBlockData(
                content=TextBlockContent(text="Here's what I found:")
            ),
            ToolUseRequestData(
                content=ToolUseRequestContent(
                    tool_input={"file_path": "/path/to/file.py"},
                    tool_name="read_file",
                    tool_use_id="tool_456"
                )
            )
        ],
        prompt_type="assistant_response",
        prompt_category="mixed",
        llm_model=LLModels.GPT_4O,
        usage=LLMUsage(input=15, output=10),
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def simple_conversation_history(
    simple_text_message: MessageThreadDTO,
    assistant_text_message: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Create a simple conversation history with user and assistant messages."""
    return [simple_text_message, assistant_text_message]


@pytest.fixture
def complex_conversation_history(
    simple_text_message: MessageThreadDTO,
    tool_use_request_message: MessageThreadDTO,
    tool_use_response_message: MessageThreadDTO,
    mixed_content_message: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Create a complex conversation history with tool use and mixed content."""
    return [
        simple_text_message,
        tool_use_request_message,
        tool_use_response_message,
        mixed_content_message,
    ]


@pytest.fixture
def conversation_with_multiple_tool_calls() -> List[MessageThreadDTO]:
    """Create conversation history with multiple tool calls and responses."""
    return [
        MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[
                TextBlockData(content=TextBlockContent(text="Can you help me with Python and JavaScript?"))
            ],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.GPT_4O,
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
                        tool_input={"language": "python"},
                        tool_name="get_language_info",
                        tool_use_id="tool_python_123"
                    )
                ),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"language": "javascript"},
                        tool_name="get_language_info",
                        tool_use_id="tool_js_456"
                    )
                )
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
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
                        tool_name="get_language_info",
                        tool_use_id="tool_python_123",
                        response={"type": "interpreted", "typing": "dynamic"}
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
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
                        tool_name="get_language_info",
                        tool_use_id="tool_js_456",
                        response={"type": "interpreted", "typing": "dynamic"}
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]


@pytest.fixture
def mock_image_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Create mock image attachment data."""
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=42,
            file_name="test_image.png",
            file_type="image/png",
            s3_key="test-bucket/test_image.png",
            status="uploaded",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        object_bytes=b"fake_image_data"
    )


@pytest.fixture
def mock_document_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Create mock document attachment data."""
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=100,
            file_name="test_document.pdf",
            file_type="application/pdf",
            s3_key="test-bucket/test_document.pdf",
            status="uploaded",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        object_bytes=b"fake_pdf_data"
    )


@pytest.fixture
def attachment_data_task_map_empty() -> Dict[int, asyncio.Task]:
    """Create an empty attachment data task map."""
    return {}


@pytest.fixture
def attachment_data_task_map_with_image(
    mock_image_attachment_data: ChatAttachmentDataWithObjectBytes,
) -> Dict[int, Any]:
    """Create attachment data task map with image."""
    async def get_image_data() -> ChatAttachmentDataWithObjectBytes:
        return mock_image_attachment_data
    
    return {42: get_image_data}


@pytest.fixture
def attachment_data_task_map_with_document(
    mock_document_attachment_data: ChatAttachmentDataWithObjectBytes,
) -> Dict[int, Any]:
    """Create attachment data task map with document."""
    async def get_document_data() -> ChatAttachmentDataWithObjectBytes:
        return mock_document_attachment_data
    
    return {100: get_document_data}


@pytest.fixture
def out_of_order_tool_conversation() -> List[MessageThreadDTO]:
    """Create conversation where tool responses arrive out of order."""
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
            message_data=[
                TextBlockData(content=TextBlockContent(text="Execute these tools"))
            ],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.GPT_4O,
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
                        tool_input={"action": "first"},
                        tool_name="tool_a",
                        tool_use_id="tool_a_123"
                    )
                ),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"action": "second"},
                        tool_name="tool_b", 
                        tool_use_id="tool_b_456"
                    )
                ),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"action": "third"},
                        tool_name="tool_c",
                        tool_use_id="tool_c_789"
                    )
                )
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
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
                        tool_name="tool_b",
                        tool_use_id="tool_b_456", 
                        response="Second tool result"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
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
                        tool_name="tool_a",
                        tool_use_id="tool_a_123",
                        response="First tool result"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
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
                        tool_name="tool_c",
                        tool_use_id="tool_c_789",
                        response="Third tool result"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]