"""
Fixtures for testing the Anthropic build_llm_payload function.

This module provides comprehensive fixtures for testing various scenarios
of the build_llm_payload function including different input combinations,
conversation turns, attachments, tools, and edge cases specific to Anthropic's
payload structure.
"""

import asyncio
import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    ExtendedThinkingContent,
    ExtendedThinkingData,
    FileContent,
    FileBlockData,
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
from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    JSONSchema,
    PromptCacheConfig,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationRole,
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
def anthropic_sample_llm_model() -> LLModels:
    """Basic LLM model for testing (Claude)."""
    return LLModels.CLAUDE_3_POINT_5_SONNET


@pytest.fixture
def anthropic_basic_user_system_messages() -> UserAndSystemMessages:
    """Basic user and system messages."""
    return UserAndSystemMessages(
        user_message="What is the weather today?",
        system_message="You are a helpful assistant."
    )


@pytest.fixture
def anthropic_empty_user_system_messages() -> UserAndSystemMessages:
    """Empty user and system messages for edge case testing."""
    return UserAndSystemMessages(
        user_message="",
        system_message=""
    )


@pytest.fixture
def anthropic_user_only_messages() -> UserAndSystemMessages:
    """User message without system message."""
    return UserAndSystemMessages(
        user_message="Hello, how are you?",
        system_message=None
    )


@pytest.fixture
def anthropic_complex_user_system_messages() -> UserAndSystemMessages:
    """Complex user and system messages with special characters."""
    return UserAndSystemMessages(
        user_message="What is 2+2? Include JSON: {\"test\": \"value\"}",
        system_message="You are a mathematical assistant. Always respond in JSON format."
    )


# =====================
# ATTACHMENT FIXTURES  
# =====================

@pytest.fixture
def anthropic_sample_image_attachment() -> Attachment:
    """Sample image attachment."""
    return Attachment(
        attachment_id=1,
        display_name="test_image.png",
        file_size=1024
    )


@pytest.fixture
def anthropic_sample_document_attachment() -> Attachment:
    """Sample document attachment."""
    return Attachment(
        attachment_id=2,
        display_name="document.pdf",
        file_size=2048
    )


@pytest.fixture
def anthropic_multiple_attachments() -> List[Attachment]:
    """Multiple attachments for testing."""
    return [
        Attachment(attachment_id=1, display_name="image1.png", file_size=1024),
        Attachment(attachment_id=2, display_name="image2.jpg", file_size=2048),
        Attachment(attachment_id=3, display_name="document.pdf", file_size=4096)
    ]


@pytest.fixture
def anthropic_sample_image_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Sample image attachment data with bytes."""
    # Create a simple base64 encoded image data
    sample_image_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=1,
            file_name="test_image.png",
            file_type="image/png",
            s3_key="test/image.png",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        object_bytes=sample_image_bytes
    )


@pytest.fixture
def anthropic_sample_document_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Sample document attachment data."""
    sample_doc_bytes = b"Sample PDF content"
    
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=ChatAttachmentsDTO(
            id=2,
            file_name="document.pdf",
            file_type="application/pdf", 
            s3_key="test/document.pdf",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        object_bytes=sample_doc_bytes
    )


@pytest.fixture
def anthropic_attachment_data_task_map_with_image(
    anthropic_sample_image_attachment: Attachment,
    anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes
) -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
    """Attachment task map with image data."""
    # Create an async mock that returns the attachment data
    mock_task = AsyncMock(return_value=anthropic_sample_image_attachment_data)
    
    return {
        anthropic_sample_image_attachment.attachment_id: mock_task
    }


@pytest.fixture  
def anthropic_attachment_data_task_map_multiple(
    anthropic_multiple_attachments: List[Attachment],
    anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    anthropic_sample_document_attachment_data: ChatAttachmentDataWithObjectBytes
) -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
    """Attachment task map with multiple attachments."""
    # Create async mock objects for each attachment
    mock_task1 = AsyncMock(return_value=anthropic_sample_image_attachment_data)
    mock_task2 = AsyncMock(return_value=anthropic_sample_image_attachment_data)  # Second image
    mock_task3 = AsyncMock(return_value=anthropic_sample_document_attachment_data)  # Document
    
    return {
        1: mock_task1,
        2: mock_task2,
        3: mock_task3
    }


@pytest.fixture
def anthropic_empty_attachment_data_task_map() -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
    """Empty attachment task map for basic scenarios."""
    return {}


# =====================
# TOOL FIXTURES
# =====================

@pytest.fixture
def anthropic_simple_tool() -> ConversationTool:
    """Simple conversation tool."""
    return ConversationTool(
        name="get_weather",
        description="Get weather information for a location",
        input_schema=JSONSchema(
            type="object",
            properties={
                "location": JSONSchema(
                    type="string",
                    description="The city and state"
                )
            },
            required=["location"]
        )
    )


@pytest.fixture
def anthropic_complex_tool() -> ConversationTool:
    """Complex conversation tool with nested schema."""
    return ConversationTool(
        name="calculate_complex",
        description="Perform complex mathematical calculations",
        input_schema=JSONSchema(
            type="object",
            properties={
                "operation": JSONSchema(
                    type="string",
                    enum=["add", "subtract", "multiply", "divide"]
                ),
                "numbers": JSONSchema(
                    type="array",
                    items=JSONSchema(type="number"),
                    min_items=2,
                    max_items=10
                ),
                "options": JSONSchema(
                    type="object",
                    properties={
                        "precision": JSONSchema(type="integer", minimum=0, maximum=10),
                        "format": JSONSchema(type="string", default="decimal")
                    }
                )
            },
            required=["operation", "numbers"]
        )
    )


@pytest.fixture
def anthropic_multiple_tools(anthropic_simple_tool: ConversationTool, anthropic_complex_tool: ConversationTool) -> List[ConversationTool]:
    """Multiple tools for testing."""
    return [anthropic_simple_tool, anthropic_complex_tool]


@pytest.fixture
def anthropic_tool_with_no_schema() -> ConversationTool:
    """Tool with empty input schema."""
    return ConversationTool(
        name="simple_action",
        description="A simple action with no parameters",
        input_schema=JSONSchema()
    )


# =====================
# TOOL USE RESPONSE FIXTURES
# =====================

@pytest.fixture
def anthropic_simple_tool_use_response() -> ToolUseResponseData:
    """Simple tool use response."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="get_weather",
            tool_use_id="tool_123456",
            response={"temperature": "25°C", "condition": "sunny"}
        )
    )


@pytest.fixture
def anthropic_string_tool_use_response() -> ToolUseResponseData:
    """Tool use response with string response."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="simple_action",
            tool_use_id="tool_789",
            response="Action completed successfully"
        )
    )


@pytest.fixture
def anthropic_complex_tool_use_response() -> ToolUseResponseData:
    """Complex tool use response."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="calculate_complex",
            tool_use_id="tool_complex_123",
            response={
                "result": 42.5,
                "operation": "multiply",
                "input_numbers": [8.5, 5],
                "metadata": {
                    "precision": 1,
                    "timestamp": "2024-01-09T18:08:50Z"
                }
            }
        )
    )


# =====================
# PREVIOUS RESPONSES FIXTURES
# =====================

@pytest.fixture
def anthropic_simple_text_message() -> MessageThreadDTO:
    """Simple text message from user."""
    return MessageThreadDTO(
        id=1,
        session_id=1,
        message_type=MessageType.QUERY,
        actor=MessageThreadActor.USER,
        data_hash="test_hash_1",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            TextBlockData(content=TextBlockContent(text="Hello, how are you?"))
        ]
    )


@pytest.fixture
def anthropic_assistant_text_response() -> MessageThreadDTO:
    """Assistant text response."""
    return MessageThreadDTO(
        id=2,
        session_id=1,
        message_type=MessageType.RESPONSE,
        actor=MessageThreadActor.ASSISTANT,
        data_hash="test_hash_2",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            TextBlockData(content=TextBlockContent(text="I'm doing well, thank you! How can I help you today?"))
        ]
    )


@pytest.fixture
def anthropic_tool_request_message() -> MessageThreadDTO:
    """Message with tool request."""
    return MessageThreadDTO(
        id=3,
        session_id=1,
        message_type=MessageType.RESPONSE,
        actor=MessageThreadActor.ASSISTANT,
        data_hash="test_hash_3",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            ToolUseRequestData(
                content=ToolUseRequestContent(
                    tool_name="get_weather",
                    tool_use_id="call_123",
                    tool_input={"location": "New York, NY"}
                )
            )
        ]
    )


@pytest.fixture
def anthropic_tool_response_message() -> MessageThreadDTO:
    """Message with tool response."""
    return MessageThreadDTO(
        id=4,
        session_id=1,
        message_type=MessageType.TOOL_RESPONSE,
        actor=MessageThreadActor.USER,
        data_hash="test_hash_4",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            ToolUseResponseData(
                content=ToolUseResponseContent(
                    tool_name="get_weather",
                    tool_use_id="call_123",
                    response={"temperature": "22°C", "condition": "cloudy"}
                )
            )
        ]
    )


@pytest.fixture
def anthropic_message_with_file_attachment() -> MessageThreadDTO:
    """Message with file attachment."""
    return MessageThreadDTO(
        id=5,
        session_id=1,
        message_type=MessageType.QUERY,
        actor=MessageThreadActor.USER,
        data_hash="test_hash_5",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            FileBlockData(content=FileContent(attachment_id=1))
        ]
    )


@pytest.fixture
def anthropic_message_with_extended_thinking() -> MessageThreadDTO:
    """Message with extended thinking content."""
    return MessageThreadDTO(
        id=6,
        session_id=1,
        message_type=MessageType.RESPONSE,
        actor=MessageThreadActor.ASSISTANT,
        data_hash="test_hash_6",
        prompt_type="test_prompt",
        prompt_category="test_category",
        llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
        call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        message_data=[
            ExtendedThinkingData(
                content=ExtendedThinkingContent(
                    type="thinking",
                    thinking="Let me think about this step by step...",
                    signature="assistant_thinking"
                )
            )
        ]
    )


@pytest.fixture
def anthropic_conversation_history(
    anthropic_simple_text_message: MessageThreadDTO,
    anthropic_assistant_text_response: MessageThreadDTO,
    anthropic_tool_request_message: MessageThreadDTO,
    anthropic_tool_response_message: MessageThreadDTO
) -> List[MessageThreadDTO]:
    """Complete conversation history."""
    return [
        anthropic_simple_text_message,
        anthropic_assistant_text_response,
        anthropic_tool_request_message,
        anthropic_tool_response_message
    ]


@pytest.fixture
def anthropic_mixed_conversation_history(
    anthropic_simple_text_message: MessageThreadDTO,
    anthropic_message_with_extended_thinking: MessageThreadDTO,
    anthropic_message_with_file_attachment: MessageThreadDTO
) -> List[MessageThreadDTO]:
    """Mixed conversation history with various content types."""
    return [
        anthropic_simple_text_message,
        anthropic_message_with_extended_thinking,
        anthropic_message_with_file_attachment
    ]


# =====================
# UNIFIED CONVERSATION TURN FIXTURES
# =====================

@pytest.fixture
def anthropic_user_text_conversation_turn() -> UserConversationTurn:
    """User conversation turn with text content."""
    return UserConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="What's the weather like today?")
        ]
    )


@pytest.fixture
def anthropic_user_multimodal_conversation_turn() -> UserConversationTurn:
    """User conversation turn with text and image content."""
    sample_image_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    
    return UserConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="What do you see in this image?"),
            UnifiedImageConversationTurnContent(
                bytes_data=sample_image_bytes,
                image_mimetype="image/png"
            )
        ]
    )


@pytest.fixture
def anthropic_user_conversation_turn_with_cache_breakpoint() -> UserConversationTurn:
    """User conversation turn with cache breakpoint."""
    return UserConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="This message should be cached.")
        ],
        cache_breakpoint=True
    )


@pytest.fixture
def anthropic_assistant_text_conversation_turn() -> AssistantConversationTurn:
    """Assistant conversation turn with text content."""
    return AssistantConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="I can help you with that!")
        ]
    )


@pytest.fixture
def anthropic_assistant_tool_request_conversation_turn() -> AssistantConversationTurn:
    """Assistant conversation turn with tool request."""
    return AssistantConversationTurn(
        content=[
            UnifiedToolRequestConversationTurnContent(
                tool_use_id="call_weather_123",
                tool_name="get_weather",
                tool_input={"location": "San Francisco, CA"}
            )
        ]
    )


@pytest.fixture
def anthropic_tool_response_conversation_turn() -> ToolConversationTurn:
    """Tool conversation turn with response."""
    return ToolConversationTurn(
        content=[
            UnifiedToolResponseConversationTurnContent(
                tool_use_id="call_weather_123",
                tool_name="get_weather",
                tool_use_response={"temperature": "18°C", "condition": "foggy"}
            )
        ]
    )


@pytest.fixture
def anthropic_unified_conversation_turns(
    anthropic_user_text_conversation_turn: UserConversationTurn,
    anthropic_assistant_tool_request_conversation_turn: AssistantConversationTurn,
    anthropic_tool_response_conversation_turn: ToolConversationTurn
):
    """Complete unified conversation turns."""
    return [
        anthropic_user_text_conversation_turn,
        anthropic_assistant_tool_request_conversation_turn,
        anthropic_tool_response_conversation_turn
    ]


@pytest.fixture
def anthropic_multimodal_unified_conversation_turns(
    anthropic_user_multimodal_conversation_turn: UserConversationTurn,
    anthropic_assistant_text_conversation_turn: AssistantConversationTurn
):
    """Unified conversation turns with multimodal content."""
    return [
        anthropic_user_multimodal_conversation_turn,
        anthropic_assistant_text_conversation_turn
    ]


# =====================
# CACHE CONFIG FIXTURES
# =====================

@pytest.fixture
def anthropic_default_cache_config() -> PromptCacheConfig:
    """Default cache configuration."""
    return PromptCacheConfig(
        tools=False,
        system_message=False,
        conversation=False
    )


@pytest.fixture
def anthropic_enabled_cache_config() -> PromptCacheConfig:
    """Enabled cache configuration."""
    return PromptCacheConfig(
        tools=True,
        system_message=True,
        conversation=True
    )


@pytest.fixture
def anthropic_partial_cache_config() -> PromptCacheConfig:
    """Partially enabled cache configuration."""
    return PromptCacheConfig(
        tools=True,
        system_message=False,
        conversation=True
    )


# =====================
# PARAMETER COMBINATION FIXTURES
# =====================

@pytest.fixture
def anthropic_minimal_build_payload_args(
    anthropic_sample_llm_model: LLModels,
    anthropic_empty_attachment_data_task_map: Dict
) -> Dict[str, Any]:
    """Minimal arguments for build_llm_payload."""
    return {
        "llm_model": anthropic_sample_llm_model,
        "attachment_data_task_map": anthropic_empty_attachment_data_task_map
    }


@pytest.fixture
def anthropic_full_build_payload_args(
    anthropic_sample_llm_model: LLModels,
    anthropic_attachment_data_task_map_with_image: Dict,
    anthropic_basic_user_system_messages: UserAndSystemMessages,
    anthropic_multiple_attachments: List[Attachment],
    anthropic_simple_tool_use_response: ToolUseResponseData,
    anthropic_conversation_history: List[MessageThreadDTO],
    anthropic_multiple_tools: List[ConversationTool],
    anthropic_enabled_cache_config: PromptCacheConfig
) -> Dict[str, Any]:
    """Full arguments for build_llm_payload."""
    return {
        "llm_model": anthropic_sample_llm_model,
        "attachment_data_task_map": anthropic_attachment_data_task_map_with_image,
        "prompt": anthropic_basic_user_system_messages,
        "attachments": anthropic_multiple_attachments,
        "tool_use_response": anthropic_simple_tool_use_response,
        "previous_responses": anthropic_conversation_history,
        "tools": anthropic_multiple_tools,
        "tool_choice": "auto",
        "feedback": "Please be more specific",
        "cache_config": anthropic_enabled_cache_config,
        "search_web": True,
        "disable_caching": False,
        "conversation_turns": []
    }


# =====================
# EDGE CASE FIXTURES
# =====================

@pytest.fixture
def anthropic_large_conversation_history() -> List[MessageThreadDTO]:
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
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_data=[
                    TextBlockData(content=TextBlockContent(text=f"Message {i}: This is a test message."))
                ]
            )
        )
    return messages


@pytest.fixture
def anthropic_conversation_with_all_content_types(
    anthropic_simple_text_message: MessageThreadDTO,
    anthropic_tool_request_message: MessageThreadDTO,
    anthropic_tool_response_message: MessageThreadDTO,
    anthropic_message_with_file_attachment: MessageThreadDTO,
    anthropic_message_with_extended_thinking: MessageThreadDTO
) -> List[MessageThreadDTO]:
    """Conversation with all possible content types."""
    return [
        anthropic_simple_text_message,
        anthropic_tool_request_message,
        anthropic_tool_response_message,
        anthropic_message_with_file_attachment,
        anthropic_message_with_extended_thinking
    ]


@pytest.fixture
def anthropic_tools_with_edge_cases() -> List[ConversationTool]:
    """Tools with edge case configurations."""
    return [
        # Tool with empty properties
        ConversationTool(
            name="empty_tool",
            description="Tool with no properties",
            input_schema=JSONSchema(type="object", properties={})
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
                                        type="object",
                                        properties={
                                            "value": JSONSchema(type="string")
                                        }
                                    )
                                }
                            )
                        }
                    )
                }
            )
        )
    ]


# =====================
# EXPECTED RESULT FIXTURES (Anthropic-specific)
# =====================

@pytest.fixture
def anthropic_expected_minimal_payload() -> Dict[str, Any]:
    """Expected payload structure for minimal input (Anthropic format)."""
    return {
        "anthropic_version": "bedrock-2023-05-31",  # Expected anthropic version
        "max_tokens": 4096,  # Based on Claude model config 
        "system": "",
        "messages": [],
        "tools": []
    }


@pytest.fixture
def anthropic_expected_payload_with_prompt() -> Dict[str, Any]:
    """Expected payload structure with prompt (Anthropic format)."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": "You are a helpful assistant.",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is the weather today?"}
                ]
            }
        ],
        "tools": []
    }


@pytest.fixture
def anthropic_expected_payload_with_tools() -> Dict[str, Any]:
    """Expected payload structure with tools (Anthropic format)."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": "",
        "messages": [],
        "tools": [
            {
                "name": "get_weather",
                "description": "Get weather information for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    }


@pytest.fixture
def anthropic_expected_payload_with_thinking() -> Dict[str, Any]:
    """Expected payload structure with thinking enabled (Anthropic format)."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": "",
        "messages": [],
        "tools": [],
        "thinking": {
            "type": "enabled",
            "budget_tokens": 25000  # Expected thinking budget
        }
    }


@pytest.fixture
def anthropic_expected_payload_with_system_cache() -> Dict[str, Any]:
    """Expected payload structure with system message caching (Anthropic format)."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": [
            {
                "type": "text",
                "text": "You are a helpful assistant.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        "messages": [],
        "tools": []
    }