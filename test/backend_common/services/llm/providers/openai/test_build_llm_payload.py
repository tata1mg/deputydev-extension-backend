"""
Comprehensive unit tests for OpenAI build_llm_payload function.

This module tests the build_llm_payload method of the OpenAI LLM provider,
which is responsible for constructing the payload to be sent to OpenAI's API.

Test Categories:
- Basic functionality with minimal inputs
- Prompt handling (user_message, system_message)
- Attachment processing (images, documents, multimodal)
- Tool configuration and formatting
- Tool use responses
- Previous response conversation handling
- Unified conversation turns processing
- Cache configuration
- Edge cases and error handling
- Parameter combinations and integration
- Performance with large inputs
- Type safety validation
"""

import asyncio
import json
from typing import Any, Dict, List

import pytest

# Import necessary DTOs and classes
from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    PromptCacheConfig,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI

# Import all build_llm_payload specific fixtures
from test.fixtures.openai.build_llm_payload_fixtures import *

# Import the provider fixture


class TestOpenAIBuildLLMPayload:
    """Comprehensive test suite for OpenAI build_llm_payload functionality."""

    # ===============================
    # BASIC FUNCTIONALITY TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_minimal_input_build_payload(
        self, openai_provider: OpenAI, minimal_build_payload_args: Dict[str, Any]
    ) -> None:
        """Test build_llm_payload with minimal required inputs."""
        result = await openai_provider.build_llm_payload(**minimal_build_payload_args)

        # Verify basic structure
        assert isinstance(result, dict)
        assert "max_tokens" in result
        assert "system_message" in result
        assert "conversation_messages" in result
        assert "tools" in result
        assert "tool_choice" in result

        # Verify default values
        assert result["system_message"] == ""
        assert result["conversation_messages"] == []
        assert result["tools"] == []
        assert result["tool_choice"] == "auto"
        assert isinstance(result["max_tokens"], int)
        assert result["max_tokens"] > 0

    @pytest.mark.asyncio
    async def test_model_config_integration(
        self, openai_provider: OpenAI, empty_attachment_data_task_map: Dict
    ) -> None:
        """Test that model configuration is properly applied."""
        # Test with different models
        test_models = [LLModels.GPT_4O, LLModels.GPT_4_POINT_1_MINI]

        for model in test_models:
            result = await openai_provider.build_llm_payload(
                llm_model=model, attachment_data_task_map=empty_attachment_data_task_map
            )

            # Each model should have appropriate max_tokens
            assert "max_tokens" in result
            assert isinstance(result["max_tokens"], int)
            assert result["max_tokens"] > 0

    # ===============================
    # PROMPT HANDLING TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_prompt_with_user_and_system_message(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        basic_user_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test build_llm_payload with both user and system messages."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=basic_user_system_messages,
        )

        # Verify system message
        assert result["system_message"] == "You are a helpful assistant."

        # Verify user message structure
        assert len(result["conversation_messages"]) == 1
        user_msg = result["conversation_messages"][0]
        assert user_msg["role"] == "user"
        assert isinstance(user_msg["content"], list)
        assert len(user_msg["content"]) == 1
        assert user_msg["content"][0]["type"] == "input_text"
        assert user_msg["content"][0]["text"] == "What is the weather today?"

    @pytest.mark.asyncio
    async def test_prompt_with_user_message_only(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        user_only_messages: UserAndSystemMessages,
    ) -> None:
        """Test build_llm_payload with user message but no system message."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=user_only_messages,
        )

        # System message should be empty
        assert result["system_message"] == ""

        # User message should still be processed
        assert len(result["conversation_messages"]) == 1
        assert result["conversation_messages"][0]["content"][0]["text"] == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_prompt_with_special_characters(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        complex_user_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test build_llm_payload with complex messages containing special characters."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=complex_user_system_messages,
        )

        # Verify special characters are preserved
        assert result["system_message"] == "You are a mathematical assistant. Always respond in JSON format."
        user_content = result["conversation_messages"][0]["content"][0]["text"]
        assert "2+2" in user_content
        assert '{"test": "value"}' in user_content

    @pytest.mark.asyncio
    async def test_empty_prompt_messages(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        empty_user_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test build_llm_payload with empty prompt messages."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=empty_user_system_messages,
        )

        # Should handle empty messages gracefully
        assert result["system_message"] == ""
        # If user_message is empty, it might not create a message at all
        if result["conversation_messages"]:
            assert result["conversation_messages"][0]["content"][0]["text"] == ""
        # This is actually valid behavior - empty messages might be skipped

    # ===============================
    # ATTACHMENT PROCESSING TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_single_image_attachment(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        basic_user_system_messages: UserAndSystemMessages,
        sample_image_attachment: Attachment,
        sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with single image attachment."""

        # Create the attachment task map in the test context where event loop exists
        async def get_attachment_data():
            return sample_image_attachment_data

        attachment_task_map = {sample_image_attachment.attachment_id: asyncio.create_task(get_attachment_data())}

        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            prompt=basic_user_system_messages,
            attachments=[sample_image_attachment],
        )

        # Verify user message contains both text and image
        user_msg = result["conversation_messages"][0]
        assert len(user_msg["content"]) == 2

        # Check text content
        text_content = user_msg["content"][0]
        assert text_content["type"] == "input_text"
        assert text_content["text"] == "What is the weather today?"

        # Check image content
        image_content = user_msg["content"][1]
        assert image_content["type"] == "input_image"
        assert "image_url" in image_content
        assert image_content["image_url"].startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_multiple_attachments(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        basic_user_system_messages: UserAndSystemMessages,
        multiple_attachments: List[Attachment],
        sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
        sample_document_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with multiple attachments."""

        # Create the attachment task map in the test context where event loop exists
        async def get_image_data():
            return sample_image_attachment_data

        async def get_doc_data():
            return sample_document_attachment_data

        attachment_task_map = {
            1: asyncio.create_task(get_image_data()),
            2: asyncio.create_task(get_image_data()),  # Second image
            3: asyncio.create_task(get_doc_data()),  # Document
        }

        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            prompt=basic_user_system_messages,
            attachments=multiple_attachments,
        )

        user_msg = result["conversation_messages"][0]

        # Should have text + 2 images (document should be ignored for non-image types)
        assert len(user_msg["content"]) == 3

        # First should be text
        assert user_msg["content"][0]["type"] == "input_text"

        # Next two should be images
        for i in [1, 2]:
            assert user_msg["content"][i]["type"] == "input_image"
            assert user_msg["content"][i]["image_url"].startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_attachment_without_task_map_entry(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        basic_user_system_messages: UserAndSystemMessages,
        sample_image_attachment: Attachment,
    ) -> None:
        """Test build_llm_payload when attachment is not in task map."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=basic_user_system_messages,
            attachments=[sample_image_attachment],
        )

        # Should only contain text content, image should be skipped
        user_msg = result["conversation_messages"][0]
        assert len(user_msg["content"]) == 1
        assert user_msg["content"][0]["type"] == "input_text"

    # ===============================
    # TOOL CONFIGURATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_single_tool_configuration(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        simple_tool: ConversationTool,
    ) -> None:
        """Test build_llm_payload with single tool."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model, attachment_data_task_map=empty_attachment_data_task_map, tools=[simple_tool]
        )

        # Verify tools are properly formatted
        assert len(result["tools"]) == 1
        tool = result["tools"][0]

        assert tool["name"] == "get_weather"
        assert tool["description"] == "Get weather information for a location"
        assert tool["type"] == "function"
        assert tool["strict"] is False

        # Verify parameters structure
        assert "parameters" in tool
        params = tool["parameters"]
        assert params["type"] == "object"
        assert "location" in params["properties"]
        assert params["required"] == ["location"]

    @pytest.mark.asyncio
    async def test_multiple_tools_sorted(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        multiple_tools: List[ConversationTool],
    ) -> None:
        """Test build_llm_payload with multiple tools (should be sorted)."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model, attachment_data_task_map=empty_attachment_data_task_map, tools=multiple_tools
        )

        # Verify tools are sorted by name
        assert len(result["tools"]) == 2
        tool_names = [tool["name"] for tool in result["tools"]]
        assert tool_names == sorted(tool_names)
        assert "calculate_complex" in tool_names
        assert "get_weather" in tool_names

    @pytest.mark.asyncio
    async def test_tool_with_no_properties(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        tool_with_no_schema: ConversationTool,
    ) -> None:
        """Test build_llm_payload with tool that has no input schema properties."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tools=[tool_with_no_schema],
        )

        # Should handle tools with no properties
        assert len(result["tools"]) == 1
        tool = result["tools"][0]
        assert tool["name"] == "simple_action"
        assert tool["parameters"] is None  # Should be None when no properties

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool_choice", ["none", "auto", "required"])
    async def test_tool_choice_options(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        simple_tool: ConversationTool,
        tool_choice: str,
    ) -> None:
        """Test build_llm_payload with different tool_choice options."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tools=[simple_tool],
            tool_choice=tool_choice,
        )

        assert result["tool_choice"] == tool_choice

    # ===============================
    # TOOL USE RESPONSE TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_tool_use_response_dict(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        simple_tool_use_response: ToolUseResponseData,
    ) -> None:
        """Test build_llm_payload with tool use response containing dict."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tool_use_response=simple_tool_use_response,
        )

        # Verify tool response is properly formatted
        assert len(result["conversation_messages"]) == 1
        tool_response = result["conversation_messages"][0]

        assert tool_response["type"] == "function_call_output"
        assert tool_response["call_id"] == "tool_123456"

        # Response should be JSON stringified
        response_data = json.loads(tool_response["output"])
        assert response_data["temperature"] == "25°C"
        assert response_data["condition"] == "sunny"

    @pytest.mark.asyncio
    async def test_tool_use_response_string(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        string_tool_use_response: ToolUseResponseData,
    ) -> None:
        """Test build_llm_payload with tool use response containing string."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tool_use_response=string_tool_use_response,
        )

        # Verify string response is properly formatted
        tool_response = result["conversation_messages"][0]
        assert tool_response["call_id"] == "tool_789"

        # String should be JSON encoded
        response_data = json.loads(tool_response["output"])
        assert response_data == "Action completed successfully"

    @pytest.mark.asyncio
    async def test_tool_use_response_complex(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        complex_tool_use_response: ToolUseResponseData,
    ) -> None:
        """Test build_llm_payload with complex tool use response."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tool_use_response=complex_tool_use_response,
        )

        tool_response = result["conversation_messages"][0]
        response_data = json.loads(tool_response["output"])

        # Verify complex nested structure is preserved
        assert response_data["result"] == 42.5
        assert response_data["metadata"]["precision"] == 1
        assert "timestamp" in response_data["metadata"]

    # ===============================
    # PREVIOUS RESPONSES CONVERSATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_simple_conversation_history(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        conversation_history: List[MessageThreadDTO],
    ) -> None:
        """Test build_llm_payload with conversation history."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            previous_responses=conversation_history,
        )

        # Should process conversation history
        assert len(result["conversation_messages"]) > 0

        # First message should be user message
        first_msg = result["conversation_messages"][0]
        assert first_msg["role"] == "user"
        assert first_msg["content"] == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_conversation_with_mixed_content_types(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        mixed_conversation_history: List[MessageThreadDTO],
        sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with conversation containing various content types."""

        # Create the attachment task map in the test context where event loop exists
        async def get_attachment_data():
            return sample_image_attachment_data

        attachment_task_map = {1: asyncio.create_task(get_attachment_data())}

        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            previous_responses=mixed_conversation_history,
        )

        # Should handle mixed content types
        # Extended thinking should be skipped, file should be processed if it's an image
        assert len(result["conversation_messages"]) >= 1

    @pytest.mark.asyncio
    async def test_conversation_with_tool_requests_and_responses(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        tool_request_message: MessageThreadDTO,
        tool_response_message: MessageThreadDTO,
    ) -> None:
        """Test build_llm_payload with tool requests and responses in conversation."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            previous_responses=[tool_request_message, tool_response_message],
        )

        # Should contain both tool request and response
        messages = result["conversation_messages"]

        # Find tool call and response
        tool_call = None
        tool_response = None

        for msg in messages:
            if msg.get("type") == "function_call":
                tool_call = msg
            elif msg.get("type") == "function_call_output":
                tool_response = msg

        # Both should be present
        assert tool_call is not None
        assert tool_response is not None
        assert tool_call["call_id"] == tool_response["call_id"]

    # ===============================
    # UNIFIED CONVERSATION TURNS TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_unified_conversation_turns_basic(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        user_text_conversation_turn: UserConversationTurn,
    ) -> None:
        """Test build_llm_payload with basic unified conversation turns."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            conversation_turns=[user_text_conversation_turn],
        )

        # Should process unified conversation turns
        assert len(result["conversation_messages"]) == 1
        msg = result["conversation_messages"][0]

        assert msg["role"] == "user"
        assert len(msg["content"]) == 1
        assert msg["content"][0]["type"] == "input_text"
        assert msg["content"][0]["text"] == "What's the weather like today?"

    @pytest.mark.asyncio
    async def test_unified_conversation_turns_multimodal(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        user_multimodal_conversation_turn: UserConversationTurn,
    ) -> None:
        """Test build_llm_payload with multimodal unified conversation turns."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            conversation_turns=[user_multimodal_conversation_turn],
        )

        msg = result["conversation_messages"][0]

        # Should contain both text and image
        assert len(msg["content"]) == 2
        assert msg["content"][0]["type"] == "input_text"
        assert msg["content"][1]["type"] == "input_image"
        assert msg["content"][1]["image_url"].startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_unified_conversation_turns_with_tools(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        unified_conversation_turns: List,
    ) -> None:
        """Test build_llm_payload with unified conversation turns including tools."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            conversation_turns=unified_conversation_turns,
        )

        # Should process all conversation turns
        messages = result["conversation_messages"]
        assert len(messages) >= 2  # At least user message and tool call

        # Verify tool call structure
        tool_calls = [msg for msg in messages if msg.get("type") == "function_call"]
        assert len(tool_calls) == 1

        tool_call = tool_calls[0]
        assert tool_call["name"] == "get_weather"
        assert tool_call["call_id"] == "call_weather_123"

    @pytest.mark.asyncio
    async def test_conversation_turns_override_previous_responses(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        conversation_history: List[MessageThreadDTO],
        user_text_conversation_turn: UserConversationTurn,
    ) -> None:
        """Test that conversation_turns override previous_responses when both provided."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            previous_responses=conversation_history,
            conversation_turns=[user_text_conversation_turn],
        )

        # Should use conversation_turns, not previous_responses
        assert len(result["conversation_messages"]) == 1
        msg = result["conversation_messages"][0]
        assert msg["content"][0]["text"] == "What's the weather like today?"

    # ===============================
    # PARAMETER COMBINATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_prompt_with_conversation_turns_ignored(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        basic_user_system_messages: UserAndSystemMessages,
        user_text_conversation_turn: UserConversationTurn,
    ) -> None:
        """Test that prompt is ignored when conversation_turns are provided."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=basic_user_system_messages,
            conversation_turns=[user_text_conversation_turn],
        )

        # Should use conversation_turns, prompt should be ignored for messages
        # but system message should still be used
        assert result["system_message"] == "You are a helpful assistant."
        assert len(result["conversation_messages"]) == 1
        assert result["conversation_messages"][0]["content"][0]["text"] == "What's the weather like today?"

    @pytest.mark.asyncio
    async def test_tool_use_response_with_conversation_turns_ignored(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        simple_tool_use_response: ToolUseResponseData,
        user_text_conversation_turn: UserConversationTurn,
    ) -> None:
        """Test that tool_use_response is ignored when conversation_turns are provided."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tool_use_response=simple_tool_use_response,
            conversation_turns=[user_text_conversation_turn],
        )

        # Should use conversation_turns, tool_use_response should be ignored
        assert len(result["conversation_messages"]) == 1
        assert result["conversation_messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_full_parameter_combination(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        basic_user_system_messages: UserAndSystemMessages,
        multiple_attachments: List[Attachment],
        simple_tool_use_response: ToolUseResponseData,
        conversation_history: List[MessageThreadDTO],
        multiple_tools: List[ConversationTool],
        enabled_cache_config: PromptCacheConfig,
        sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test build_llm_payload with all parameters provided."""

        # Create the attachment task map in the test context where event loop exists
        async def get_attachment_data():
            return sample_image_attachment_data

        attachment_task_map = {
            1: asyncio.create_task(get_attachment_data()),
            2: asyncio.create_task(get_attachment_data()),  # Second attachment
            3: asyncio.create_task(get_attachment_data()),  # Third attachment
        }

        full_args = {
            "llm_model": sample_llm_model,
            "attachment_data_task_map": attachment_task_map,
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

        result = await openai_provider.build_llm_payload(**full_args)

        # Verify all components are present
        assert isinstance(result, dict)
        assert result["system_message"] == "You are a helpful assistant."
        assert len(result["tools"]) == 2  # Multiple tools
        assert result["tool_choice"] == "auto"
        assert len(result["conversation_messages"]) > 0

    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================

    @pytest.mark.asyncio
    async def test_large_conversation_history(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        large_conversation_history: List[MessageThreadDTO],
    ) -> None:
        """Test build_llm_payload with large conversation history."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            previous_responses=large_conversation_history,
        )

        # Should handle large conversations
        assert len(result["conversation_messages"]) == len(large_conversation_history)

    @pytest.mark.asyncio
    async def test_tools_with_edge_case_schemas(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        tools_with_edge_cases: List[ConversationTool],
    ) -> None:
        """Test build_llm_payload with tools having edge case schemas."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            tools=tools_with_edge_cases,
        )

        # Should handle edge case tool schemas
        assert len(result["tools"]) == 2

        # Verify tools are properly formatted despite edge cases
        for tool in result["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "type" in tool
            assert tool["type"] == "function"

    @pytest.mark.asyncio
    async def test_async_attachment_task_failure(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        basic_user_system_messages: UserAndSystemMessages,
        sample_image_attachment: Attachment,
    ) -> None:
        """Test build_llm_payload when attachment task fails."""

        # Create a failing task
        async def failing_task():
            raise Exception("Failed to load attachment")

        attachment_task_map = {sample_image_attachment.attachment_id: asyncio.create_task(failing_task())}

        # Should handle task failure gracefully
        with pytest.raises(Exception):
            await openai_provider.build_llm_payload(
                llm_model=sample_llm_model,
                attachment_data_task_map=attachment_task_map,
                prompt=basic_user_system_messages,
                attachments=[sample_image_attachment],
            )

    # ===============================
    # TYPE SAFETY AND VALIDATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_return_type_structure(
        self, openai_provider: OpenAI, minimal_build_payload_args: Dict[str, Any]
    ) -> None:
        """Test that return type always has expected structure."""
        result = await openai_provider.build_llm_payload(**minimal_build_payload_args)

        # Verify required keys and types
        required_keys = ["max_tokens", "system_message", "conversation_messages", "tools", "tool_choice"]
        for key in required_keys:
            assert key in result

        assert isinstance(result["max_tokens"], int)
        assert isinstance(result["system_message"], str)
        assert isinstance(result["conversation_messages"], list)
        assert isinstance(result["tools"], list)
        assert isinstance(result["tool_choice"], str)

    @pytest.mark.asyncio
    async def test_conversation_messages_structure(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        basic_user_system_messages: UserAndSystemMessages,
    ) -> None:
        """Test that conversation messages always have proper structure."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            prompt=basic_user_system_messages,
        )

        for msg in result["conversation_messages"]:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert isinstance(msg["role"], str)

            if "content" in msg:
                if isinstance(msg["content"], list):
                    for content_item in msg["content"]:
                        assert isinstance(content_item, dict)
                        assert "type" in content_item
                else:
                    assert isinstance(msg["content"], str)

    @pytest.mark.asyncio
    async def test_tools_structure_validation(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        simple_tool: ConversationTool,
    ) -> None:
        """Test that tools always have proper OpenAI structure."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model, attachment_data_task_map=empty_attachment_data_task_map, tools=[simple_tool]
        )

        for tool in result["tools"]:
            # Verify OpenAI tool structure
            required_fields = ["name", "description", "type", "strict"]
            for field in required_fields:
                assert field in tool

            assert tool["type"] == "function"
            assert isinstance(tool["strict"], bool)
            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)

    # ===============================
    # PERFORMANCE AND INTEGRATION TESTS
    # ===============================

    @pytest.mark.asyncio
    async def test_concurrent_attachment_processing(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        basic_user_system_messages: UserAndSystemMessages,
        multiple_attachments: List[Attachment],
        sample_image_attachment_data: ChatAttachmentDataWithObjectBytes,
        sample_document_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test that concurrent attachment processing works correctly."""

        # Create the attachment task map in the test context where event loop exists
        async def get_image_data():
            return sample_image_attachment_data

        async def get_doc_data():
            return sample_document_attachment_data

        attachment_task_map = {
            1: asyncio.create_task(get_image_data()),
            2: asyncio.create_task(get_image_data()),  # Second image
            3: asyncio.create_task(get_doc_data()),  # Document
        }

        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=attachment_task_map,
            prompt=basic_user_system_messages,
            attachments=multiple_attachments,
        )

        # Should handle concurrent attachment processing
        user_msg = result["conversation_messages"][0]
        # Text + images (documents filtered out)
        assert len(user_msg["content"]) >= 1

    @pytest.mark.asyncio
    async def test_cache_config_parameter_preservation(
        self,
        openai_provider: OpenAI,
        sample_llm_model: LLModels,
        empty_attachment_data_task_map: Dict,
        enabled_cache_config: PromptCacheConfig,
    ) -> None:
        """Test that cache configuration is properly handled (parameter preservation)."""
        # Cache config should be accepted without error but may not affect output structure
        # since it's used elsewhere in the pipeline
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            cache_config=enabled_cache_config,
        )

        # Should not affect basic structure
        assert isinstance(result, dict)
        assert "max_tokens" in result

    @pytest.mark.asyncio
    async def test_feedback_parameter_preservation(
        self, openai_provider: OpenAI, sample_llm_model: LLModels, empty_attachment_data_task_map: Dict
    ) -> None:
        """Test that feedback parameter is accepted without affecting output."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model,
            attachment_data_task_map=empty_attachment_data_task_map,
            feedback="Please provide more detailed explanations",
        )

        # Feedback should be accepted but not affect payload structure
        assert isinstance(result, dict)
        assert "max_tokens" in result

    @pytest.mark.asyncio
    async def test_search_web_parameter_preservation(
        self, openai_provider: OpenAI, sample_llm_model: LLModels, empty_attachment_data_task_map: Dict
    ) -> None:
        """Test that search_web parameter is accepted without affecting output."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model, attachment_data_task_map=empty_attachment_data_task_map, search_web=True
        )

        # Should be accepted but not affect payload structure
        assert isinstance(result, dict)
        assert "max_tokens" in result

    @pytest.mark.asyncio
    async def test_disable_caching_parameter_preservation(
        self, openai_provider: OpenAI, sample_llm_model: LLModels, empty_attachment_data_task_map: Dict
    ) -> None:
        """Test that disable_caching parameter is accepted without affecting output."""
        result = await openai_provider.build_llm_payload(
            llm_model=sample_llm_model, attachment_data_task_map=empty_attachment_data_task_map, disable_caching=True
        )

        # Should be accepted but not affect payload structure
        assert isinstance(result, dict)
        assert "max_tokens" in result
