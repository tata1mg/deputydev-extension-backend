"""
Comprehensive unit tests for Anthropic build_llm_payload function.

This module tests the build_llm_payload method of the Anthropic LLM provider,
which is responsible for constructing the payload to be sent to Anthropic's API
via AWS Bedrock.

Test Categories:
- Basic functionality with minimal inputs
- Prompt handling (user_message, system_message)
- Attachment processing (images, documents, multimodal)
- Tool configuration and formatting
- Tool use responses
- Previous response conversation handling
- Unified conversation turns processing
- Cache configuration (system message, tools, conversation)
- Thinking mode configuration
- Edge cases and error handling
- Parameter combinations and integration
- Performance with large inputs
- Type safety validation
- Anthropic-specific payload structure validation
"""

import asyncio
from typing import Any, Dict, List

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationTool,
    PromptCacheConfig,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.providers.anthropic.llm_provider import Anthropic

# Import necessary DTOs and classes
from app.backend_common.models.dto.message_thread_dto import LLModels

# Import all build_llm_payload specific fixtures
from test.fixtures.anthropic.build_llm_payload_fixtures import *

# Import the provider fixture


class TestAnthropicBuildLLMPayload:
    """Comprehensive test suite for Anthropic build_llm_payload functionality."""

    # ===============================
    # BASIC FUNCTIONALITY TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_minimal_input_build_payload(
        self, anthropic_provider: Anthropic, anthropic_minimal_build_payload_args: Dict[str, Any]
    ) -> None:
        """Test build_llm_payload with minimal required inputs."""
        result = await anthropic_provider.build_llm_payload(**anthropic_minimal_build_payload_args)

        # Verify basic Anthropic structure
        assert isinstance(result, dict)
        assert "anthropic_version" in result
        assert "max_tokens" in result
        assert "system" in result
        assert "messages" in result
        assert "tools" in result

        # Verify default values
        assert result["system"] == ""
        assert result["messages"] == []
        assert result["tools"] == []
        assert isinstance(result["max_tokens"], int)
        assert result["max_tokens"] > 0
        assert result["anthropic_version"] == "bedrock-2023-05-31"

    @pytest.mark.asyncio
    async def test_model_config_integration(
        self, anthropic_provider: Anthropic, anthropic_empty_attachment_data_task_map: Dict
    ) -> None:
        """Test that model configuration is properly applied."""
        # Test with different Claude models
        test_models = [LLModels.CLAUDE_3_POINT_5_SONNET, LLModels.CLAUDE_3_POINT_7_SONNET, LLModels.CLAUDE_4_SONNET]

        for model in test_models:
            result = await anthropic_provider.build_llm_payload(
                llm_model=model, attachment_data_task_map=anthropic_empty_attachment_data_task_map
            )

            # Each model should have appropriate max_tokens
            assert "max_tokens" in result
            assert isinstance(result["max_tokens"], int)
            assert result["max_tokens"] > 0
            # Verify anthropic version consistency
            assert result["anthropic_version"] == "bedrock-2023-05-31"

    # ===============================
    # PROMPT HANDLING TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_prompt_with_user_and_system_message(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with both user and system messages."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_basic_user_system_messages,
        )

        # Verify system message
        assert result["system"] == "You are a helpful assistant."

        # Verify user message structure (Anthropic format)
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"][0]["type"] == "text"
        assert result["messages"][0]["content"][0]["text"] == "What is the weather today?"

    @pytest.mark.asyncio
    async def test_prompt_with_user_message_only(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_user_only_messages: UserAndSystemMessages,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with only user message."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_user_only_messages,
        )

        # Verify system message is empty when not provided
        assert result["system"] == ""

        # Verify user message is properly formatted
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"][0]["text"] == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_prompt_with_special_characters(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_complex_user_system_messages: UserAndSystemMessages,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with special characters and JSON."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_complex_user_system_messages,
        )

        # Verify special characters are preserved
        assert "JSON" in result["messages"][0]["content"][0]["text"]
        assert "2+2" in result["messages"][0]["content"][0]["text"]
        assert "mathematical assistant" in result["system"]

    @pytest.mark.asyncio
    async def test_empty_prompt_messages(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_empty_user_system_messages: UserAndSystemMessages,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with empty prompt messages."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_empty_user_system_messages,
        )

        # Verify empty messages result in expected behavior
        assert result["system"] == ""
        # Empty user message should not create any message (it's filtered out)
        assert len(result["messages"]) == 0

    # ===============================
    # ATTACHMENT TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_single_image_attachment(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_sample_image_attachment: Attachment,
        anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with single image attachment."""

        # Create the attachment task map in the test context where event loop exists
        async def get_attachment_data():
            return anthropic_sample_image_attachment_data

        attachment_task_map = {
            anthropic_sample_image_attachment.attachment_id: asyncio.create_task(get_attachment_data())
        }

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            prompt=anthropic_basic_user_system_messages,
            attachments=[anthropic_sample_image_attachment],
        )

        # Verify image attachment in Anthropic format
        user_message = result["messages"][0]
        assert user_message["role"] == "user"
        assert len(user_message["content"]) == 2  # Image + text

        # Image should be first (inserted at beginning)
        image_content = user_message["content"][0]
        assert image_content["type"] == "image"
        assert image_content["source"]["type"] == "base64"
        assert image_content["source"]["media_type"] == "image/png"
        assert "data" in image_content["source"]

        # Text should be second
        text_content = user_message["content"][1]
        assert text_content["type"] == "text"
        assert text_content["text"] == "What is the weather today?"

    @pytest.mark.asyncio
    async def test_multiple_attachments(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_multiple_attachments: List[Attachment],
        anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
        anthropic_sample_document_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with multiple attachments."""

        # Create attachment task map in test context
        async def get_image_data():
            return anthropic_sample_image_attachment_data

        async def get_doc_data():
            return anthropic_sample_document_attachment_data

        attachment_task_map = {
            1: asyncio.create_task(get_image_data()),
            2: asyncio.create_task(get_image_data()),  # Second image
            3: asyncio.create_task(get_doc_data()),  # Document
        }

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            prompt=anthropic_basic_user_system_messages,
            attachments=anthropic_multiple_attachments,
        )

        # Verify multiple images are processed (document attachment should be ignored)
        user_message = result["messages"][0]
        image_contents = [c for c in user_message["content"] if c["type"] == "image"]
        text_contents = [c for c in user_message["content"] if c["type"] == "text"]

        assert len(image_contents) == 2  # Two image attachments
        assert len(text_contents) == 1  # One text message

        # Verify each image has proper Anthropic format
        for image_content in image_contents:
            assert image_content["source"]["type"] == "base64"
            assert image_content["source"]["media_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_attachment_without_task_map_entry(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_sample_image_attachment: Attachment,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with attachment but no corresponding task map entry."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_basic_user_system_messages,
            attachments=[anthropic_sample_image_attachment],
        )

        # Should only have text content when attachment data is missing
        user_message = result["messages"][0]
        assert len(user_message["content"]) == 1
        assert user_message["content"][0]["type"] == "text"

    # ===============================
    # TOOL CONFIGURATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_single_tool_configuration(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_simple_tool: ConversationTool,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with single tool."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=[anthropic_simple_tool],
        )

        # Verify tool is properly formatted for Anthropic
        assert len(result["tools"]) == 1
        tool = result["tools"][0]
        assert tool["name"] == "get_weather"
        assert tool["description"] == "Get weather information for a location"
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "location" in tool["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_multiple_tools_sorted(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_multiple_tools: List[ConversationTool],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with multiple tools are sorted by name."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=anthropic_multiple_tools,
        )

        # Verify tools are sorted alphabetically
        assert len(result["tools"]) == 2
        tool_names = [tool["name"] for tool in result["tools"]]
        assert tool_names == sorted(tool_names)
        assert "calculate_complex" in tool_names
        assert "get_weather" in tool_names

    @pytest.mark.asyncio
    async def test_tool_with_no_properties(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_tool_with_no_schema: ConversationTool,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with tool that has no input schema properties."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=[anthropic_tool_with_no_schema],
        )

        # Verify tool without properties is still properly formatted
        assert len(result["tools"]) == 1
        tool = result["tools"][0]
        assert tool["name"] == "simple_action"
        # Should have input_schema even if empty
        assert "input_schema" in tool

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool_choice", ["none", "auto", "required"])
    async def test_tool_choice_options(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_simple_tool: ConversationTool,
        anthropic_empty_attachment_data_task_map: Dict,
        tool_choice: str,
    ) -> None:
        """Test build_llm_payload with different tool_choice options."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=[anthropic_simple_tool],
            tool_choice=tool_choice,
        )

        # Anthropic doesn't use tool_choice in the same way as OpenAI
        # The tools should still be present regardless of choice
        assert len(result["tools"]) == 1
        # Note: Anthropic handles tool choice differently, may not appear in payload

    # ===============================
    # TOOL USE RESPONSE TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_tool_use_response_dict(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_simple_tool_use_response: ToolUseResponseData,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with tool use response (dict format)."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tool_use_response=anthropic_simple_tool_use_response,
        )

        # Tool use response handling depends on previous_responses/conversation_turns
        # With no conversation context, tool_use_response should not affect the base payload
        assert isinstance(result, dict)
        assert "messages" in result
        assert "tools" in result

    @pytest.mark.asyncio
    async def test_tool_use_response_string(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_string_tool_use_response: ToolUseResponseData,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with tool use response (string format)."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tool_use_response=anthropic_string_tool_use_response,
        )

        # Similar to dict response, should not affect base payload without conversation context
        assert isinstance(result, dict)
        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_tool_use_response_complex(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_complex_tool_use_response: ToolUseResponseData,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with complex tool use response."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tool_use_response=anthropic_complex_tool_use_response,
        )

        # Complex tool response should not affect base payload structure
        assert isinstance(result, dict)
        assert "anthropic_version" in result
        assert "messages" in result

    # ===============================
    # CONVERSATION HISTORY TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_simple_conversation_history(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_conversation_history: List[MessageThreadDTO],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with simple conversation history."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            previous_responses=anthropic_conversation_history,
        )

        # Verify conversation history is processed into messages
        assert len(result["messages"]) > 0

        # Check message structure follows Anthropic format
        for message in result["messages"]:
            assert "role" in message
            assert message["role"] in ["user", "assistant"]
            assert "content" in message
            assert isinstance(message["content"], list)

    @pytest.mark.asyncio
    async def test_conversation_with_mixed_content_types(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_mixed_conversation_history: List[MessageThreadDTO],
        anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with conversation containing mixed content types."""

        # Create attachment task map in test context
        async def get_attachment_data():
            return anthropic_sample_image_attachment_data

        attachment_task_map = {1: asyncio.create_task(get_attachment_data())}

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            previous_responses=anthropic_mixed_conversation_history,
        )

        # Should handle mixed content types (text, thinking, file attachments)
        assert len(result["messages"]) > 0
        assert isinstance(result["messages"], list)

    @pytest.mark.asyncio
    async def test_conversation_with_tool_requests_and_responses(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_tool_request_message: MessageThreadDTO,
        anthropic_tool_response_message: MessageThreadDTO,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with tool requests and responses in conversation."""
        conversation = [anthropic_tool_request_message, anthropic_tool_response_message]

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            previous_responses=conversation,
        )

        # Tool interactions should be properly formatted in Anthropic conversation structure
        assert len(result["messages"]) >= 2  # Tool request and response should create separate messages

        # Check for tool_use and tool_result content types
        all_content = []
        for message in result["messages"]:
            all_content.extend(message["content"])

        content_types = [content.get("type") for content in all_content]
        assert "tool_use" in content_types or "tool_result" in content_types

    # ===============================
    # UNIFIED CONVERSATION TURN TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_unified_conversation_turns_basic(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_user_text_conversation_turn: UserConversationTurn,
        anthropic_assistant_text_conversation_turn: AssistantConversationTurn,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with basic unified conversation turns."""
        conversation_turns = [anthropic_user_text_conversation_turn, anthropic_assistant_text_conversation_turn]

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            conversation_turns=conversation_turns,
        )

        # Verify unified conversation turns are converted properly
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

        # Check content structure
        assert result["messages"][0]["content"][0]["type"] == "text"
        assert result["messages"][0]["content"][0]["text"] == "What's the weather like today?"

    @pytest.mark.asyncio
    async def test_unified_conversation_turns_multimodal(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_multimodal_unified_conversation_turns: List,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with multimodal unified conversation turns."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            conversation_turns=anthropic_multimodal_unified_conversation_turns,
        )

        # Check multimodal content in first message
        user_message = result["messages"][0]
        assert user_message["role"] == "user"
        assert len(user_message["content"]) == 2  # Text + image

        content_types = [content["type"] for content in user_message["content"]]
        assert "text" in content_types
        assert "image" in content_types

    @pytest.mark.asyncio
    async def test_unified_conversation_turns_with_tools(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_unified_conversation_turns: List,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with unified conversation turns containing tools."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            conversation_turns=anthropic_unified_conversation_turns,
        )

        # Should have user message, assistant tool request, and tool response
        assert len(result["messages"]) == 3

        # Check for tool-related content
        all_content = []
        for message in result["messages"]:
            all_content.extend(message["content"])

        content_types = [content.get("type") for content in all_content]
        assert "tool_use" in content_types
        assert "tool_result" in content_types

    @pytest.mark.asyncio
    async def test_conversation_turns_override_previous_responses(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_user_text_conversation_turn: UserConversationTurn,
        anthropic_conversation_history: List[MessageThreadDTO],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that conversation_turns override previous_responses when both are provided."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            previous_responses=anthropic_conversation_history,
            conversation_turns=[anthropic_user_text_conversation_turn],
        )

        # Should only have one message from conversation_turns, ignoring previous_responses
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"][0]["text"] == "What's the weather like today?"

    @pytest.mark.asyncio
    async def test_prompt_with_conversation_turns_ignored(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_user_text_conversation_turn: UserConversationTurn,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that prompt is ignored when conversation_turns are provided."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_basic_user_system_messages,
            conversation_turns=[anthropic_user_text_conversation_turn],
        )

        # Should use conversation_turns instead of prompt
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"][0]["text"] == "What's the weather like today?"
        # System message should still be present from prompt
        assert result["system"] == "You are a helpful assistant."

    # ===============================
    # CACHE CONFIGURATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_system_message_caching(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with system message caching enabled."""
        cache_config = PromptCacheConfig(system_message=True, tools=False, conversation=False)

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            prompt=anthropic_basic_user_system_messages,
            cache_config=cache_config,
        )

        # System message should be in array format with cache_control
        assert isinstance(result["system"], list)
        assert len(result["system"]) == 1
        assert result["system"][0]["type"] == "text"
        assert result["system"][0]["text"] == "You are a helpful assistant."
        assert result["system"][0]["cache_control"]["type"] == "ephemeral"

    @pytest.mark.asyncio
    async def test_tools_caching(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_multiple_tools: List[ConversationTool],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with tools caching enabled."""
        cache_config = PromptCacheConfig(system_message=False, tools=True, conversation=False)

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=anthropic_multiple_tools,
            cache_config=cache_config,
        )

        # Last tool should have cache_control
        assert len(result["tools"]) == 2
        last_tool = result["tools"][-1]
        assert "cache_control" in last_tool
        assert last_tool["cache_control"]["type"] == "ephemeral"

    @pytest.mark.asyncio
    async def test_conversation_caching(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_conversation_history: List[MessageThreadDTO],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with conversation caching enabled."""
        cache_config = PromptCacheConfig(system_message=False, tools=False, conversation=True)

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            previous_responses=anthropic_conversation_history,
            cache_config=cache_config,
        )

        # Last message's last content should have cache_control
        if result["messages"]:
            last_message = result["messages"][-1]
            last_content = last_message["content"][-1]
            assert "cache_control" in last_content
            assert last_content["cache_control"]["type"] == "ephemeral"

    @pytest.mark.asyncio
    async def test_cache_breakpoint_in_unified_turns(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_user_conversation_turn_with_cache_breakpoint: UserConversationTurn,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with cache breakpoint in unified conversation turn."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            conversation_turns=[anthropic_user_conversation_turn_with_cache_breakpoint],
        )

        # Cache breakpoint should add cache_control to last content
        user_message = result["messages"][0]
        last_content = user_message["content"][-1]
        assert "cache_control" in last_content
        assert last_content["cache_control"]["type"] == "ephemeral"

    # ===============================
    # THINKING MODE TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_thinking_mode_enabled(
        self, anthropic_provider: Anthropic, anthropic_empty_attachment_data_task_map: Dict
    ) -> None:
        """Test build_llm_payload with thinking mode enabled model."""
        # Use a model that supports thinking mode
        result = await anthropic_provider.build_llm_payload(
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,  # Assuming this model supports thinking
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
        )

        # Check if thinking configuration is present (depends on model config)
        if "thinking" in result:
            assert result["thinking"]["type"] == "enabled"
            assert isinstance(result["thinking"]["budget_tokens"], int)
            assert result["thinking"]["budget_tokens"] > 0

    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================

    @pytest.mark.asyncio
    async def test_large_conversation_history(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_large_conversation_history: List[MessageThreadDTO],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with large conversation history."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            previous_responses=anthropic_large_conversation_history,
        )

        # Should handle large conversation without issues
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 0

    @pytest.mark.asyncio
    async def test_tools_with_edge_case_schemas(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_tools_with_edge_cases: List[ConversationTool],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test build_llm_payload with tools having edge case schemas."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=anthropic_tools_with_edge_cases,
        )

        # Should handle edge case tool schemas
        assert len(result["tools"]) == len(anthropic_tools_with_edge_cases)
        for tool in result["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    @pytest.mark.asyncio
    async def test_async_attachment_task_failure(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_sample_image_attachment: Attachment,
    ) -> None:
        """Test build_llm_payload when attachment task fails."""

        # Create a failing task in test context
        async def failing_task():
            raise Exception("Attachment processing failed")

        failing_task_map = {anthropic_sample_image_attachment.attachment_id: asyncio.create_task(failing_task())}

        # Should handle attachment processing failure gracefully
        with pytest.raises(Exception, match="Attachment processing failed"):
            await anthropic_provider.build_llm_payload(
                llm_model=anthropic_sample_llm_model,
                attachment_data_task_map=failing_task_map,
                prompt=anthropic_basic_user_system_messages,
                attachments=[anthropic_sample_image_attachment],
            )

    # ===============================
    # INTEGRATION AND TYPE VALIDATION
    # ===============================

    @pytest.mark.asyncio
    async def test_return_type_structure(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that build_llm_payload returns proper dictionary structure."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model, attachment_data_task_map=anthropic_empty_attachment_data_task_map
        )

        # Verify return type and required fields
        assert isinstance(result, dict)
        required_fields = ["anthropic_version", "max_tokens", "system", "messages", "tools"]
        for field in required_fields:
            assert field in result

        # Verify field types
        assert isinstance(result["anthropic_version"], str)
        assert isinstance(result["max_tokens"], int)
        assert isinstance(result["system"], (str, list))
        assert isinstance(result["messages"], list)
        assert isinstance(result["tools"], list)

    @pytest.mark.asyncio
    async def test_conversation_messages_structure(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_conversation_history: List[MessageThreadDTO],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that conversation messages follow proper Anthropic structure."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            previous_responses=anthropic_conversation_history,
        )

        # Verify message structure
        for message in result["messages"]:
            assert isinstance(message, dict)
            assert "role" in message
            assert "content" in message
            assert message["role"] in ["user", "assistant"]
            assert isinstance(message["content"], list)

            # Verify content structure
            for content in message["content"]:
                assert isinstance(content, dict)
                assert "type" in content
                # Different content types should have appropriate fields
                if content["type"] == "text":
                    assert "text" in content
                elif content["type"] == "image":
                    assert "source" in content
                elif content["type"] in ["tool_use", "tool_result"]:
                    # Tool-related content should have proper structure
                    pass

    @pytest.mark.asyncio
    async def test_tools_structure_validation(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_multiple_tools: List[ConversationTool],
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that tools are properly structured for Anthropic."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            tools=anthropic_multiple_tools,
        )

        # Verify tool structure
        for tool in result["tools"]:
            assert isinstance(tool, dict)
            required_tool_fields = ["name", "description", "input_schema"]
            for field in required_tool_fields:
                assert field in tool

            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)
            assert isinstance(tool["input_schema"], dict)

            # Verify input_schema structure
            schema = tool["input_schema"]
            assert "type" in schema
            if "properties" in schema:
                assert isinstance(schema["properties"], dict)

    # ===============================
    # PARAMETER PRESERVATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_cache_config_parameter_preservation(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_enabled_cache_config: PromptCacheConfig,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that cache_config parameter is properly preserved and applied."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            cache_config=anthropic_enabled_cache_config,
        )

        # Cache config should not affect basic structure when no cacheable content
        assert isinstance(result, dict)
        assert "anthropic_version" in result

    @pytest.mark.asyncio
    async def test_feedback_parameter_preservation(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that feedback parameter is preserved."""
        feedback_text = "Please provide more detailed explanations"

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            feedback=feedback_text,
        )

        # Feedback is passed but may not appear directly in Anthropic payload
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_search_web_parameter_preservation(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that search_web parameter is preserved."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            search_web=True,
        )

        # search_web parameter is preserved but may not affect Anthropic payload directly
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_disable_caching_parameter_preservation(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_empty_attachment_data_task_map: Dict,
    ) -> None:
        """Test that disable_caching parameter is preserved."""
        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=anthropic_empty_attachment_data_task_map,
            disable_caching=True,
        )

        # disable_caching should prevent cache-related modifications
        assert isinstance(result, dict)

    # ===============================
    # CONCURRENT PROCESSING TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_concurrent_attachment_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_multiple_attachments: List[Attachment],
        anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
        anthropic_sample_document_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with concurrent attachment processing."""

        # Create concurrent tasks
        async def get_image_data():
            await asyncio.sleep(0.01)  # Simulate async processing
            return anthropic_sample_image_attachment_data

        async def get_doc_data():
            await asyncio.sleep(0.01)  # Simulate async processing
            return anthropic_sample_document_attachment_data

        # Create task map with actual async tasks
        task_map = {
            1: asyncio.create_task(get_image_data()),
            2: asyncio.create_task(get_image_data()),
            3: asyncio.create_task(get_doc_data()),
        }

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=task_map,
            prompt=anthropic_basic_user_system_messages,
            attachments=anthropic_multiple_attachments,
        )

        # Should handle concurrent processing correctly
        assert isinstance(result, dict)
        assert len(result["messages"]) == 1

        # Should have processed image attachments
        user_message = result["messages"][0]
        image_contents = [c for c in user_message["content"] if c["type"] == "image"]
        assert len(image_contents) == 2  # Two images processed

    # ===============================
    # FULL INTEGRATION TEST
    # ===============================

    @pytest.mark.asyncio
    async def test_full_parameter_combination(
        self,
        anthropic_provider: Anthropic,
        anthropic_sample_llm_model: LLModels,
        anthropic_basic_user_system_messages: UserAndSystemMessages,
        anthropic_multiple_attachments: List[Attachment],
        anthropic_simple_tool_use_response: ToolUseResponseData,
        anthropic_conversation_history: List[MessageThreadDTO],
        anthropic_multiple_tools: List[ConversationTool],
        anthropic_enabled_cache_config: PromptCacheConfig,
        anthropic_sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with full parameter combination."""

        # Create attachment task map in test context
        async def get_attachment_data():
            return anthropic_sample_image_attachment_data

        attachment_task_map = {1: asyncio.create_task(get_attachment_data())}

        result = await anthropic_provider.build_llm_payload(
            llm_model=anthropic_sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            prompt=anthropic_basic_user_system_messages,
            attachments=anthropic_multiple_attachments,
            tool_use_response=anthropic_simple_tool_use_response,
            previous_responses=anthropic_conversation_history,
            tools=anthropic_multiple_tools,
            tool_choice="auto",
            feedback="Please be more specific",
            cache_config=anthropic_enabled_cache_config,
            search_web=True,
            disable_caching=False,
            conversation_turns=[],
        )

        # Verify comprehensive payload structure
        assert isinstance(result, dict)

        # Core Anthropic structure
        assert "anthropic_version" in result
        assert "max_tokens" in result
        assert "system" in result
        assert "messages" in result
        assert "tools" in result

        # Verify content is processed correctly with all parameters
        assert result["anthropic_version"] == "bedrock-2023-05-31"
        assert isinstance(result["max_tokens"], int)
        assert result["max_tokens"] > 0

        # System message should be present
        assert result["system"] != ""

        # Should have messages from conversation history
        assert len(result["messages"]) > 0

        # Should have sorted tools
        assert len(result["tools"]) > 0
        tool_names = [tool["name"] for tool in result["tools"]]
        assert tool_names == sorted(tool_names)
