"""
Fixtures for testing the OpenAI build_llm_payload function.

This module provides comprehensive fixtures for testing various scenarios
of the build_llm_payload function including different input combinations,
conversation turns, attachments, tools, and edge cases.
"""

import asyncio
import base64
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO
from app.backend_common.models.dto.message_thread_dto import (
    ExtendedThinkingContent,
    ExtendedThinkingData,
    FileBlockData,
    FileContent,
    LLModels,
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
    Attachment,
    ChatAttachmentDataWithObjectBytes,
)
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    JSONSchema,
    PromptCacheConfig,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedImageConversationTurnContent,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)

# =====================
# BASIC INPUT FIXTURES
# =====================


@pytest.fixture
def sample_llm_model() -> LLModels:
    """Basic LLM model for testing."""
    return LLModels.GPT_4O


@pytest.fixture
def basic_user_system_messages() -> UserAndSystemMessages:
    """Basic user and system messages."""
    return UserAndSystemMessages(
        user_message="What is the weather today?", system_message="You are a helpful assistant."
    )


@pytest.fixture
def empty_user_system_messages() -> UserAndSystemMessages:
    """Empty user and system messages for edge case testing."""
    return UserAndSystemMessages(user_message="", system_message="")


@pytest.fixture
def user_only_messages() -> UserAndSystemMessages:
    """User message without system message."""
    return UserAndSystemMessages(user_message="Hello, how are you?", system_message=None)


@pytest.fixture
def complex_user_system_messages() -> UserAndSystemMessages:
    """Complex user and system messages with special characters."""
    return UserAndSystemMessages(
        user_message='What is 2+2? Include JSON: {"test": "value"}',
        system_message="You are a mathematical assistant. Always respond in JSON format.",
    )


# =====================
# ATTACHMENT FIXTURES
# =====================


@pytest.fixture
def sample_image_attachment() -> Attachment:
    """Sample image attachment."""
    return Attachment(attachment_id=1, display_name="test_image.png", file_size=1024)


@pytest.fixture
def sample_document_attachment() -> Attachment:
    """Sample document attachment."""
    return Attachment(attachment_id=2, display_name="document.pdf", file_size=2048)


@pytest.fixture
def multiple_attachments() -> List[Attachment]:
    """Multiple attachments for testing."""
    return [
        Attachment(attachment_id=1, display_name="image1.png", file_size=1024),
        Attachment(attachment_id=2, display_name="image2.jpg", file_size=2048),
        Attachment(attachment_id=3, display_name="document.pdf", file_size=4096),
    ]


@pytest.fixture
def sample_image_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Sample image attachment data with bytes."""
    # Create a simple base64 encoded image data
    sample_image_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=1,
            file_name="test_image.png",
            file_type="image/png",
            s3_key="test/image.png",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        object_bytes=sample_image_bytes,
    )


@pytest.fixture
def sample_document_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Sample document attachment data."""
    sample_doc_bytes = b"Sample PDF content"

    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=2,
            file_name="document.pdf",
            file_type="application/pdf",
            s3_key="test/document.pdf",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        object_bytes=sample_doc_bytes,
    )


@pytest.fixture
def attachment_data_task_map_with_image(
    sample_image_attachment: Attachment, sample_image_attachment_data: ChatAttachmentDataWithObjectBytes
) -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
    """Attachment task map with image data."""

    # Create a mock that behaves like an awaitable task
    async def mock_awaitable():
        return sample_image_attachment_data

    # Create a mock task object with the proper behavior
    mock_task = MagicMock()
    mock_task.__await__ = lambda: mock_awaitable().__await__()

    return {sample_image_attachment.attachment_id: mock_task}


@pytest.fixture
def attachment_data_task_map_multiple(
    multiple_attachments: List[Attachment],
    sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    sample_document_attachment_data: ChatAttachmentDataWithObjectBytes,
) -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
    """Attachment task map with multiple attachments."""

    # Create mock awaitables for each attachment
    async def mock_image_awaitable():
        return sample_image_attachment_data

    async def mock_doc_awaitable():
        return sample_document_attachment_data

    # Create mock task objects
    mock_task1 = MagicMock()
    mock_task1.__await__ = lambda: mock_image_awaitable().__await__()

    mock_task2 = MagicMock()
    mock_task2.__await__ = lambda: mock_image_awaitable().__await__()

    mock_task3 = MagicMock()
    mock_task3.__await__ = lambda: mock_doc_awaitable().__await__()

    return {
        1: mock_task1,
        2: mock_task2,  # Second image
        3: mock_task3,  # Document
    }


@pytest.fixture
def empty_attachment_data_task_map() -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
    """Empty attachment task map for basic scenarios."""
    return {}


# =====================
# TOOL FIXTURES
# =====================


@pytest.fixture
def simple_tool() -> ConversationTool:
    """Simple conversation tool."""
    return ConversationTool(
        name="get_weather",
        description="Get weather information for a location",
        input_schema=JSONSchema(
            type="object",
            properties={"location": JSONSchema(type="string", description="The city and state")},
            required=["location"],
        ),
    )


@pytest.fixture
def complex_tool() -> ConversationTool:
    """Complex conversation tool with nested schema."""
    return ConversationTool(
        name="calculate_complex",
        description="Perform complex mathematical calculations",
        input_schema=JSONSchema(
            type="object",
            properties={
                "operation": JSONSchema(type="string", enum=["add", "subtract", "multiply", "divide"]),
                "numbers": JSONSchema(type="array", items=JSONSchema(type="number"), min_items=2, max_items=10),
                "options": JSONSchema(
                    type="object",
                    properties={
                        "precision": JSONSchema(type="integer", minimum=0, maximum=10),
                        "format": JSONSchema(type="string", default="decimal"),
                    },
                ),
            },
            required=["operation", "numbers"],
        ),
    )


@pytest.fixture
def multiple_tools(simple_tool: ConversationTool, complex_tool: ConversationTool) -> List[ConversationTool]:
    """Multiple tools for testing."""
    return [simple_tool, complex_tool]


@pytest.fixture
def tool_with_no_schema() -> ConversationTool:
    """Tool with empty input schema."""
    return ConversationTool(
        name="simple_action", description="A simple action with no parameters", input_schema=JSONSchema()
    )


# =====================
# TOOL USE RESPONSE FIXTURES
# =====================


@pytest.fixture
def simple_tool_use_response() -> ToolUseResponseData:
    """Simple tool use response."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="get_weather", tool_use_id="tool_123456", response={"temperature": "25°C", "condition": "sunny"}
        )
    )


@pytest.fixture
def string_tool_use_response() -> ToolUseResponseData:
    """Tool use response with string response."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="simple_action", tool_use_id="tool_789", response="Action completed successfully"
        )
    )


@pytest.fixture
def complex_tool_use_response() -> ToolUseResponseData:
    """Complex tool use response."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="calculate_complex",
            tool_use_id="tool_complex_123",
            response={
                "result": 42.5,
                "operation": "multiply",
                "input_numbers": [8.5, 5],
                "metadata": {"precision": 1, "timestamp": "2024-01-09T18:08:50Z"},
            },
        )
    )


# =====================
# PREVIOUS RESPONSES FIXTURES
# =====================


@pytest.fixture
def simple_text_message() -> MessageThreadDTO:
    """Simple text message from user."""
    return MessageThreadDTO(
        id=1,
        session_id=1,
        message_type=MessageType.QUERY,
        actor=MessageThreadActor.USER,
        data_hash="test_hash_1",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.GPT_4O,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[TextBlockData(content=TextBlockContent(text="Hello, how are you?"))],
    )


@pytest.fixture
def assistant_text_response() -> MessageThreadDTO:
    """Assistant text response."""
    return MessageThreadDTO(
        id=2,
        session_id=1,
        message_type=MessageType.RESPONSE,
        actor=MessageThreadActor.ASSISTANT,
        data_hash="test_hash_2",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.GPT_4O,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            TextBlockData(content=TextBlockContent(text="I'm doing well, thank you! How can I help you today?"))
        ],
    )


@pytest.fixture
def tool_request_message() -> MessageThreadDTO:
    """Message with tool request."""
    return MessageThreadDTO(
        id=3,
        session_id=1,
        message_type=MessageType.RESPONSE,
        actor=MessageThreadActor.ASSISTANT,
        data_hash="test_hash_3",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.GPT_4O,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            ToolUseRequestData(
                content=ToolUseRequestContent(
                    tool_name="get_weather", tool_use_id="call_123", tool_input={"location": "New York, NY"}
                )
            )
        ],
    )


@pytest.fixture
def tool_response_message() -> MessageThreadDTO:
    """Message with tool response."""
    return MessageThreadDTO(
        id=4,
        session_id=1,
        message_type=MessageType.TOOL_RESPONSE,
        actor=MessageThreadActor.USER,
        data_hash="test_hash_4",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.GPT_4O,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            ToolUseResponseData(
                content=ToolUseResponseContent(
                    tool_name="get_weather",
                    tool_use_id="call_123",
                    response={"temperature": "22°C", "condition": "cloudy"},
                )
            )
        ],
    )


@pytest.fixture
def message_with_file_attachment() -> MessageThreadDTO:
    """Message with file attachment."""
    return MessageThreadDTO(
        id=5,
        session_id=1,
        message_type=MessageType.QUERY,
        actor=MessageThreadActor.USER,
        data_hash="test_hash_5",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.GPT_4O,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[FileBlockData(content=FileContent(attachment_id=1))],
    )


@pytest.fixture
def message_with_extended_thinking() -> MessageThreadDTO:
    """Message with extended thinking content."""
    return MessageThreadDTO(
        id=6,
        session_id=1,
        message_type=MessageType.RESPONSE,
        actor=MessageThreadActor.ASSISTANT,
        data_hash="test_hash_6",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.GPT_4O,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            ExtendedThinkingData(
                content=ExtendedThinkingContent(
                    type="thinking", thinking="Let me think about this step by step...", signature="assistant_thinking"
                )
            )
        ],
    )


@pytest.fixture
def conversation_history(
    simple_text_message: MessageThreadDTO,
    assistant_text_response: MessageThreadDTO,
    tool_request_message: MessageThreadDTO,
    tool_response_message: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Complete conversation history."""
    return [simple_text_message, assistant_text_response, tool_request_message, tool_response_message]


@pytest.fixture
def mixed_conversation_history(
    simple_text_message: MessageThreadDTO,
    message_with_extended_thinking: MessageThreadDTO,
    message_with_file_attachment: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Mixed conversation history with various content types."""
    return [simple_text_message, message_with_extended_thinking, message_with_file_attachment]


# =====================
# UNIFIED CONVERSATION TURN FIXTURES
# =====================


@pytest.fixture
def user_text_conversation_turn() -> UserConversationTurn:
    """User conversation turn with text content."""
    return UserConversationTurn(content=[UnifiedTextConversationTurnContent(text="What's the weather like today?")])


@pytest.fixture
def user_multimodal_conversation_turn() -> UserConversationTurn:
    """User conversation turn with text and image content."""
    sample_image_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    return UserConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="What do you see in this image?"),
            UnifiedImageConversationTurnContent(bytes_data=sample_image_bytes, image_mimetype="image/png"),
        ]
    )


@pytest.fixture
def assistant_text_conversation_turn() -> AssistantConversationTurn:
    """Assistant conversation turn with text content."""
    return AssistantConversationTurn(content=[UnifiedTextConversationTurnContent(text="I can help you with that!")])


@pytest.fixture
def assistant_tool_request_conversation_turn() -> AssistantConversationTurn:
    """Assistant conversation turn with tool request."""
    return AssistantConversationTurn(
        content=[
            UnifiedToolRequestConversationTurnContent(
                tool_use_id="call_weather_123", tool_name="get_weather", tool_input={"location": "San Francisco, CA"}
            )
        ]
    )


@pytest.fixture
def tool_response_conversation_turn() -> ToolConversationTurn:
    """Tool conversation turn with response."""
    return ToolConversationTurn(
        content=[
            UnifiedToolResponseConversationTurnContent(
                tool_use_id="call_weather_123",
                tool_name="get_weather",
                tool_use_response={"temperature": "18°C", "condition": "foggy"},
            )
        ]
    )


@pytest.fixture
def unified_conversation_turns(
    user_text_conversation_turn: UserConversationTurn,
    assistant_tool_request_conversation_turn: AssistantConversationTurn,
    tool_response_conversation_turn: ToolConversationTurn,
):
    """Complete unified conversation turns."""
    return [user_text_conversation_turn, assistant_tool_request_conversation_turn, tool_response_conversation_turn]


@pytest.fixture
def multimodal_unified_conversation_turns(
    user_multimodal_conversation_turn: UserConversationTurn, assistant_text_conversation_turn: AssistantConversationTurn
):
    """Unified conversation turns with multimodal content."""
    return [user_multimodal_conversation_turn, assistant_text_conversation_turn]


# =====================
# CACHE CONFIG FIXTURES
# =====================


@pytest.fixture
def default_cache_config() -> PromptCacheConfig:
    """Default cache configuration."""
    return PromptCacheConfig(tools=False, system_message=False, conversation=False)


@pytest.fixture
def enabled_cache_config() -> PromptCacheConfig:
    """Enabled cache configuration."""
    return PromptCacheConfig(tools=True, system_message=True, conversation=True)


@pytest.fixture
def partial_cache_config() -> PromptCacheConfig:
    """Partially enabled cache configuration."""
    return PromptCacheConfig(tools=True, system_message=False, conversation=True)


# =====================
# PARAMETER COMBINATION FIXTURES
# =====================


@pytest.fixture
def minimal_build_payload_args(sample_llm_model: LLModels, empty_attachment_data_task_map: Dict) -> Dict[str, Any]:
    """Minimal arguments for build_llm_payload."""
    return {"llm_model": sample_llm_model, "attachment_data_task_map": empty_attachment_data_task_map}


@pytest.fixture
def full_build_payload_args(
    sample_llm_model: LLModels,
    attachment_data_task_map_with_image: Dict,
    basic_user_system_messages: UserAndSystemMessages,
    multiple_attachments: List[Attachment],
    simple_tool_use_response: ToolUseResponseData,
    conversation_history: List[MessageThreadDTO],
    multiple_tools: List[ConversationTool],
    enabled_cache_config: PromptCacheConfig,
) -> Dict[str, Any]:
    """Full arguments for build_llm_payload."""
    return {
        "llm_model": sample_llm_model,
        "attachment_data_task_map": attachment_data_task_map_with_image,
        "prompt": basic_user_system_messages,
        "attachments": multiple_attachments,
        "tool_use_response": simple_tool_use_response,
        "previous_responses": conversation_history,
        "tools": multiple_tools,
        "tool_choice": "auto",
        "feedback": "Please be more specific",
        "cache_config": enabled_cache_config,
        "search_web": True,
        "disable_caching": False,
        "conversation_turns": [],
    }


# =====================
# EDGE CASE FIXTURES
# =====================


@pytest.fixture
def large_conversation_history() -> List[MessageThreadDTO]:
    """Large conversation history for stress testing."""
    messages = []
    for i in range(50):
        # Alternate between user and assistant messages
        actor = MessageThreadActor.USER if i % 2 == 0 else MessageThreadActor.ASSISTANT
        message_type = MessageType.QUERY if actor == MessageThreadActor.USER else MessageType.RESPONSE

        messages.append(
            MessageThreadDTO(
                id=100 + i,
                session_id=1,
                message_type=message_type,
                actor=actor,
                data_hash=f"test_hash_{100 + i}",
                prompt_type="test_prompt",
                prompt_category="test_category",
                llm_model=LLModels.GPT_4O,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_data=[TextBlockData(content=TextBlockContent(text=f"Message {i}: This is a test message."))],
            )
        )
    return messages


@pytest.fixture
def conversation_with_all_content_types(
    simple_text_message: MessageThreadDTO,
    tool_request_message: MessageThreadDTO,
    tool_response_message: MessageThreadDTO,
    message_with_file_attachment: MessageThreadDTO,
    message_with_extended_thinking: MessageThreadDTO,
) -> List[MessageThreadDTO]:
    """Conversation with all possible content types."""
    return [
        simple_text_message,
        tool_request_message,
        tool_response_message,
        message_with_file_attachment,
        message_with_extended_thinking,
    ]


@pytest.fixture
def tools_with_edge_cases() -> List[ConversationTool]:
    """Tools with edge case configurations."""
    return [
        # Tool with empty properties
        ConversationTool(
            name="empty_tool",
            description="Tool with no properties",
            input_schema=JSONSchema(type="object", properties={}),
        ),
        # Tool with complex nested schema
        ConversationTool(
            name="nested_tool",
            description="Tool with deeply nested schema",
            input_schema=JSONSchema(
                type="object",
                properties={
                    "config": JSONSchema(
                        type="object",
                        properties={
                            "settings": JSONSchema(
                                type="object",
                                properties={
                                    "advanced": JSONSchema(
                                        type="object", properties={"value": JSONSchema(type="string")}
                                    )
                                },
                            )
                        },
                    )
                },
            ),
        ),
    ]


# =====================
# EXPECTED RESULT FIXTURES
# =====================


@pytest.fixture
def expected_minimal_payload() -> Dict[str, Any]:
    """Expected payload structure for minimal input."""
    return {
        "max_tokens": 4000,  # Based on GPT_4O model config
        "system_message": "",
        "conversation_messages": [],
        "tools": [],
        "tool_choice": "auto",
    }


@pytest.fixture
def expected_payload_with_prompt() -> Dict[str, Any]:
    """Expected payload structure with prompt."""
    return {
        "max_tokens": 4000,
        "system_message": "You are a helpful assistant.",
        "conversation_messages": [
            {"role": "user", "content": [{"type": "input_text", "text": "What is the weather today?"}]}
        ],
        "tools": [],
        "tool_choice": "auto",
    }


@pytest.fixture
def expected_payload_with_tools() -> Dict[str, Any]:
    """Expected payload structure with tools."""
    return {
        "max_tokens": 4000,
        "system_message": "",
        "conversation_messages": [],
        "tools": [
            {
                "name": "get_weather",
                "description": "Get weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "The city and state"}},
                    "required": ["location"],
                },
                "type": "function",
                "strict": False,
            }
        ],
        "tool_choice": "auto",
    }
