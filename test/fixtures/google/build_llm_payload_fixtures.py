"""
Build LLM payload fixtures for Google/Gemini tests.

This module contains fixtures for testing the build_llm_payload method,
including various payload configurations and scenarios.
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationTool,
    PromptCacheConfig,
    UserAndSystemMessages,
)

from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO
from app.backend_common.models.dto.message_thread_dto import (
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


@pytest.fixture
def simple_user_and_system_messages() -> UserAndSystemMessages:
    """Simple user and system messages for basic testing."""
    return UserAndSystemMessages(
        system_message="You are a helpful assistant.", user_message="What is the weather like today?"
    )


@pytest.fixture
def complex_user_and_system_messages() -> UserAndSystemMessages:
    """Complex user and system messages with detailed instructions."""
    return UserAndSystemMessages(
        system_message="""You are a highly skilled software engineer and coding assistant.
        You have access to various development tools and can help with:
        - Code review and analysis
        - Bug fixing and debugging
        - Performance optimization
        - Best practices recommendations
        
        Always provide clear explanations and use tools when appropriate.""",
        user_message="""I need help optimizing this Python function for better performance.
        Can you analyze it and suggest improvements? Here's the function:
        
        def slow_function(data):
            result = []
            for item in data:
                if item % 2 == 0:
                    result.append(item * 2)
            return result
        """,
    )


@pytest.fixture
def empty_user_and_system_messages() -> UserAndSystemMessages:
    """Empty user and system messages."""
    return UserAndSystemMessages(system_message="", user_message="")


@pytest.fixture
def simple_conversation_tool() -> ConversationTool:
    """Simple conversation tool for testing."""
    from deputydev_core.llm_handler.dataclasses.main import JSONSchema

    return ConversationTool(
        name="search_web",
        description="Search the web for information",
        input_schema=JSONSchema(
            type="object",
            properties={
                "query": JSONSchema(type="string", description="Search query"),
                "limit": JSONSchema(type="integer", default=10, description="Maximum number of results"),
            },
            required=["query"],
        ),
    )


@pytest.fixture
def complex_conversation_tools() -> List[ConversationTool]:
    """Multiple complex conversation tools."""
    from deputydev_core.llm_handler.dataclasses.main import JSONSchema

    return [
        ConversationTool(
            name="get_weather",
            description="Get current weather information for a location",
            input_schema=JSONSchema(
                type="object",
                properties={
                    "location": JSONSchema(type="string", description="Location to get weather for"),
                    "units": JSONSchema(type="string", default="celsius", description="Temperature units"),
                    "include_forecast": JSONSchema(type="boolean", default=False, description="Include forecast"),
                },
                required=["location"],
            ),
        ),
        ConversationTool(
            name="analyze_code",
            description="Analyze code for issues, performance, and best practices",
            input_schema=JSONSchema(
                type="object",
                properties={
                    "code": JSONSchema(type="string", description="Code to analyze"),
                    "language": JSONSchema(type="string", description="Programming language"),
                    "analysis_type": JSONSchema(type="string", description="Type of analysis"),
                    "max_issues": JSONSchema(type="integer", description="Maximum issues to report"),
                },
                required=["code", "language", "analysis_type"],
            ),
        ),
        ConversationTool(
            name="file_operations",
            description="Perform file operations like read, write, or modify files",
            input_schema=JSONSchema(
                type="object",
                properties={
                    "file_path": JSONSchema(type="string", description="Path to the file"),
                    "operation": JSONSchema(type="string", description="Operation to perform"),
                    "content": JSONSchema(type="string", description="File content for write operations"),
                },
                required=["file_path", "operation"],
            ),
        ),
    ]


@pytest.fixture
def simple_attachments() -> List[Attachment]:
    """Simple attachments for testing."""
    return [
        Attachment(attachment_id=1, name="test_document.pdf", attachment_type="document"),
        Attachment(attachment_id=2, name="screenshot.png", attachment_type="image"),
    ]


@pytest.fixture
def mock_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Mock attachment data with object bytes."""
    attachment_dto = ChatAttachmentsDTO(
        id=1,
        file_name="test_document.pdf",
        file_type="application/pdf",
        s3_key="docs/test_document.pdf",
        status="uploaded",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=attachment_dto.model_dump(),
        object_bytes=b"mock_document_bytes",
    )


@pytest.fixture
def mock_image_attachment_data() -> ChatAttachmentDataWithObjectBytes:
    """Mock image attachment data."""
    attachment_dto = ChatAttachmentsDTO(
        id=2,
        file_name="screenshot.png",
        file_type="image/png",
        s3_key="images/screenshot.png",
        status="uploaded",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return ChatAttachmentDataWithObjectBytes(
        attachment_metadata=attachment_dto.model_dump(),
        object_bytes=b"mock_image_bytes",
    )


@pytest.fixture
def simple_attachment_data_task_map() -> Dict[int, Any]:
    """Simple attachment data task map."""

    async def get_attachment_1():
        attachment_dto = ChatAttachmentsDTO(
            id=1,
            file_name="test.pdf",
            file_type="application/pdf",
            s3_key="test.pdf",
            status="uploaded",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return ChatAttachmentDataWithObjectBytes(
            attachment_metadata=attachment_dto.model_dump(),
            object_bytes=b"mock_pdf_bytes",
        )

    async def get_attachment_2():
        attachment_dto = ChatAttachmentsDTO(
            id=2,
            file_name="image.png",
            file_type="image/png",
            s3_key="image.png",
            status="uploaded",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return ChatAttachmentDataWithObjectBytes(
            attachment_metadata=attachment_dto.model_dump(),
            object_bytes=b"mock_image_bytes",
        )

    # Return the coroutine functions, not tasks, since event loop might not be running yet
    return {1: get_attachment_1, 2: get_attachment_2}


@pytest.fixture
def simple_previous_responses() -> List[MessageThreadDTO]:
    """Simple previous responses for testing."""
    return [
        MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[TextBlockData(content=TextBlockContent(text="Hello, how can you help me?"))],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
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
            message_data=[TextBlockData(content=TextBlockContent(text="I can help you with various tasks!"))],
            prompt_type="assistant_response",
            prompt_category="general",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def complex_previous_responses() -> List[MessageThreadDTO]:
    """Complex previous responses with tools."""
    return [
        MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[TextBlockData(content=TextBlockContent(text="What's the weather in New York?"))],
            prompt_type="user_query",
            prompt_category="weather",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
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
                TextBlockData(content=TextBlockContent(text="I'll check the weather for you.")),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"location": "New York", "units": "celsius"},
                        tool_name="get_weather",
                        tool_use_id="weather_123",
                    )
                ),
            ],
            prompt_type="assistant_response",
            prompt_category="weather",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
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
                        tool_name="get_weather",
                        tool_use_id="weather_123",
                        response={"temperature": "22°C", "condition": "sunny", "humidity": "65%"},
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="weather",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def simple_tool_use_response() -> ToolUseResponseData:
    """Simple tool use response for testing."""
    return ToolUseResponseData(
        content=ToolUseResponseContent(
            tool_name="search_function",
            tool_use_id="search_123",
            response={"results": ["Result 1", "Result 2", "Result 3"], "total": 3},
        )
    )


@pytest.fixture
def default_cache_config() -> PromptCacheConfig:
    """Default cache configuration."""
    return PromptCacheConfig(tools=True, system_message=True, conversation=True)


@pytest.fixture
def disabled_cache_config() -> PromptCacheConfig:
    """Disabled cache configuration."""
    return PromptCacheConfig(tools=False, system_message=False, conversation=False)


@pytest.fixture
def empty_attachment_data_task_map() -> Dict[int, Any]:
    """Empty attachment data task map."""
    return {}


@pytest.fixture
def mock_model_config_gemini_pro() -> Dict[str, Any]:
    """Mock model configuration for Gemini Pro."""
    return {"NAME": "gemini-2.5-pro", "MAX_TOKENS": 8192, "THINKING_BUDGET_TOKENS": 4096, "TEMPERATURE": 0.7}


@pytest.fixture
def mock_model_config_gemini_flash() -> Dict[str, Any]:
    """Mock model configuration for Gemini Flash."""
    return {"NAME": "gemini-2.5-flash", "MAX_TOKENS": 4096, "THINKING_BUDGET_TOKENS": 2048, "TEMPERATURE": 0.5}
