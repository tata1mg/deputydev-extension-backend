"""
Test cases for remaining Anthropic provider methods.

This module contains comprehensive test cases for the methods in the Anthropic class
that were not covered by existing test files, following the .deputydevrules guidelines.
"""

import base64
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationRole,
    ConversationTurn,
    LLMCallResponseTypes,
    NonStreamingResponse,
    StreamingResponse,
)
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationTurn,
    UserConversationTurn,
)
from deputydev_core.llm_handler.providers.anthropic.llm_provider import Anthropic

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
    LLMUsage,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
)
from test.fixtures.anthropic.remaining_methods_fixtures import *


class TestAnthropicConversationTurnConversion:
    """Test suite for Anthropic conversation turn conversion methods."""

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_user_conversation_turn_basic(
        self, anthropic_provider: Anthropic, sample_user_conversation_turn: UserConversationTurn
    ) -> None:
        """Test basic user conversation turn conversion."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_user_conversation_turn(
            sample_user_conversation_turn
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.USER
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert result.content[0]["text"] == "Hello, how can you help me?"

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_user_conversation_turn_with_image(
        self, anthropic_provider: Anthropic, user_conversation_turn_with_image: UserConversationTurn
    ) -> None:
        """Test user conversation turn with image content."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_user_conversation_turn(
            user_conversation_turn_with_image
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.USER
        assert len(result.content) == 2

        # Check text content
        text_content = next(c for c in result.content if c["type"] == "text")
        assert text_content["text"] == "What do you see in this image?"

        # Check image content
        image_content = next(c for c in result.content if c["type"] == "image")
        assert image_content["source"]["type"] == "base64"
        assert image_content["source"]["media_type"] == "image/jpeg"
        assert image_content["source"]["data"] == base64.b64encode(b"fake_image_data_here").decode("utf-8")

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_user_conversation_turn_with_cache_breakpoint(
        self, anthropic_provider: Anthropic, user_conversation_turn_with_cache_breakpoint: UserConversationTurn
    ) -> None:
        """Test user conversation turn with cache breakpoint."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_user_conversation_turn(
            user_conversation_turn_with_cache_breakpoint
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.USER
        assert len(result.content) == 1
        assert "cache_control" in result.content[0]
        assert result.content[0]["cache_control"]["type"] == "ephemeral"

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_assistant_conversation_turn_basic(
        self, anthropic_provider: Anthropic, sample_assistant_conversation_turn: AssistantConversationTurn
    ) -> None:
        """Test basic assistant conversation turn conversion."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_assistant_conversation_turn(
            sample_assistant_conversation_turn
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.ASSISTANT
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        assert result.content[0]["text"] == "I can help you with various tasks!"

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_assistant_conversation_turn_with_tool_request(
        self, anthropic_provider: Anthropic, assistant_conversation_turn_with_tool_request: AssistantConversationTurn
    ) -> None:
        """Test assistant conversation turn with tool request."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_assistant_conversation_turn(
            assistant_conversation_turn_with_tool_request
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.ASSISTANT
        assert len(result.content) == 2

        # Check text content
        text_content = next(c for c in result.content if c["type"] == "text")
        assert text_content["text"] == "Let me search for that information."

        # Check tool use content
        tool_content = next(c for c in result.content if c["type"] == "tool_use")
        assert tool_content["name"] == "search_web"
        assert tool_content["id"] == "tool_123"
        assert tool_content["input"] == {"query": "python programming"}

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_tool_conversation_turn_single(
        self, anthropic_provider: Anthropic, sample_tool_conversation_turn: ToolConversationTurn
    ) -> None:
        """Test tool conversation turn conversion with single response."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_tool_conversation_turn(
            sample_tool_conversation_turn
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.USER
        assert len(result.content) == 1
        assert result.content[0]["type"] == "tool_result"
        assert result.content[0]["tool_use_id"] == "tool_123"
        assert json.loads(result.content[0]["content"]) == {"results": "Python is a programming language"}

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turn_from_tool_conversation_turn_multiple(
        self, anthropic_provider: Anthropic, multiple_tool_responses_turn: ToolConversationTurn
    ) -> None:
        """Test tool conversation turn conversion with multiple responses."""
        result = anthropic_provider._get_anthropic_conversation_turn_from_tool_conversation_turn(
            multiple_tool_responses_turn
        )

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.USER
        assert len(result.content) == 2

        # Check first tool result
        tool_result_1 = result.content[0]
        assert tool_result_1["type"] == "tool_result"
        assert tool_result_1["tool_use_id"] == "tool_1"
        assert json.loads(tool_result_1["content"]) == {"result": "First result"}

        # Check second tool result
        tool_result_2 = result.content[1]
        assert tool_result_2["type"] == "tool_result"
        assert tool_result_2["tool_use_id"] == "tool_2"
        assert json.loads(tool_result_2["content"]) == {"result": "Second result"}

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turns_from_conversation_turns_mixed(
        self, anthropic_provider: Anthropic, mixed_unified_conversation_turns: List[UnifiedConversationTurn]
    ) -> None:
        """Test conversion of mixed conversation turn types."""
        result = anthropic_provider._get_anthropic_conversation_turns_from_conversation_turns(
            mixed_unified_conversation_turns
        )

        assert isinstance(result, list)
        assert len(result) == 3

        # Check user turn
        assert result[0].role == ConversationRole.USER
        assert result[0].content[0]["type"] == "text"

        # Check assistant turn
        assert result[1].role == ConversationRole.ASSISTANT
        assert result[1].content[0]["type"] == "text"

        # Check tool turn
        assert result[2].role == ConversationRole.USER
        assert result[2].content[0]["type"] == "tool_result"

    @pytest.mark.asyncio
    async def test_get_anthropic_conversation_turns_from_conversation_turns_complex(
        self, anthropic_provider: Anthropic, complex_unified_conversation_turns: List[UnifiedConversationTurn]
    ) -> None:
        """Test conversion of complex conversation turns with multiple content types."""
        result = anthropic_provider._get_anthropic_conversation_turns_from_conversation_turns(
            complex_unified_conversation_turns
        )

        assert isinstance(result, list)
        assert len(result) == 3

        # Check user turn with image
        user_turn = result[0]
        assert user_turn.role == ConversationRole.USER
        assert len(user_turn.content) == 2
        text_content = next(c for c in user_turn.content if c["type"] == "text")
        image_content = next(c for c in user_turn.content if c["type"] == "image")
        assert text_content["text"] == "What do you see in this image?"
        assert image_content["source"]["media_type"] == "image/jpeg"

        # Check assistant turn with tool request
        assistant_turn = result[1]
        assert assistant_turn.role == ConversationRole.ASSISTANT
        assert len(assistant_turn.content) == 2
        tool_content = next(c for c in assistant_turn.content if c["type"] == "tool_use")
        assert tool_content["name"] == "search_web"

        # Check tool turn with multiple responses
        tool_turn = result[2]
        assert tool_turn.role == ConversationRole.USER
        assert len(tool_turn.content) == 2


class TestAnthropicRegionAndServiceClient:
    """Test suite for region selection and service client management."""

    @pytest.mark.asyncio
    async def test_get_best_region_for_query_session_distribution(
        self, anthropic_provider: Anthropic, sample_model_config: Dict[str, Any]
    ) -> None:
        """Test region selection distributes sessions across regions."""
        # Test different session IDs to verify distribution
        session_ids = [1, 2, 3, 4, 5]
        regions = []

        for session_id in session_ids:
            region, model_identifier = await anthropic_provider._get_best_region_for_query(
                session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
            )
            regions.append(region)
            assert model_identifier == "anthropic.claude-3-sonnet-20240229-v1:0"

        # Verify that different regions are selected
        unique_regions = set(regions)
        assert len(unique_regions) > 1  # Should use multiple regions

        # Verify modulo distribution
        expected_regions = ["us-east-1", "us-west-2", "eu-west-1"]
        for i, session_id in enumerate(session_ids):
            expected_index = session_id % len(expected_regions)
            expected_region = expected_regions[expected_index]
            assert regions[i] == expected_region

    @pytest.mark.asyncio
    async def test_get_best_region_for_query_consistency(
        self, anthropic_provider: Anthropic, sample_model_config: Dict[str, Any]
    ) -> None:
        """Test that same session ID always returns same region."""
        session_id = 42

        # Call multiple times with same session ID
        results = []
        for _ in range(3):
            region, model_identifier = await anthropic_provider._get_best_region_for_query(
                session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
            )
            results.append((region, model_identifier))

        # All results should be identical
        assert len(set(results)) == 1
        assert results[0][0] == "us-east-1"  # 42 % 3 = 0, so first region (index 0)

    @pytest.mark.asyncio
    async def test_get_service_client_and_model_name_client_caching(
        self, anthropic_provider: Anthropic, sample_model_config: Dict[str, Any]
    ) -> None:
        """Test that service clients are cached by region."""
        with patch("deputydev_core.llm_handler.providers.anthropic.llm_provider.BedrockServiceClient") as mock_bedrock:
            mock_client = MagicMock()
            mock_bedrock.return_value = mock_client

            session_id = 1

            # First call should create client
            client1, model_id1 = await anthropic_provider._get_service_client_and_model_name(
                session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
            )

            assert client1 is mock_client
            assert model_id1 == "anthropic.claude-3-sonnet-20240229-v1:0"
            assert mock_bedrock.call_count == 1

            # Second call with same session (same region) should reuse client
            client2, model_id2 = await anthropic_provider._get_service_client_and_model_name(
                session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
            )

            assert client2 is mock_client
            assert model_id2 == "anthropic.claude-3-sonnet-20240229-v1:0"
            assert mock_bedrock.call_count == 1  # No additional calls

            # Call with different session (different region) should create new client
            session_id_different = 2
            client3, model_id3 = await anthropic_provider._get_service_client_and_model_name(
                session_id_different, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
            )

            assert model_id3 == "anthropic.claude-3-sonnet-20240229-v1:0"
            assert mock_bedrock.call_count == 2  # New client created

    @pytest.mark.asyncio
    async def test_get_service_client_and_model_name_region_consistency(
        self, anthropic_provider: Anthropic, sample_model_config: Dict[str, Any]
    ) -> None:
        """Test that service client method uses consistent region selection."""
        with patch("deputydev_core.llm_handler.providers.anthropic.llm_provider.BedrockServiceClient") as mock_bedrock:
            mock_client = MagicMock()
            mock_bedrock.return_value = mock_client

            session_id = 5

            # Call the method
            await anthropic_provider._get_service_client_and_model_name(
                session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
            )

            # Verify the client was created with the correct region
            expected_region = "eu-west-1"  # 5 % 3 = 2, so third region (index 2)
            mock_bedrock.assert_called_once_with(region_name=expected_region)


class TestAnthropicNonStreamingResponse:
    """Test suite for non-streaming response parsing."""

    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_text_only(
        self, anthropic_provider: Anthropic, sample_invoke_model_response: Dict[str, Any]
    ) -> None:
        """Test parsing non-streaming response with text content."""
        result = await anthropic_provider._parse_non_streaming_response(sample_invoke_model_response)

        assert isinstance(result, NonStreamingResponse)
        assert result.type == LLMCallResponseTypes.NON_STREAMING
        assert len(result.content) == 1

        content_block = result.content[0]
        assert isinstance(content_block, TextBlockData)
        assert content_block.type == ContentBlockCategory.TEXT_BLOCK
        assert isinstance(content_block.content, TextBlockContent)
        assert content_block.content.text == "Hello! How can I help you today?"

        assert isinstance(result.usage, LLMUsage)
        assert result.usage.input == 15
        assert result.usage.output == 8
        assert result.usage.cache_read == 0
        assert result.usage.cache_write == 0

    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_with_tool_use(
        self, anthropic_provider: Anthropic, tool_use_invoke_model_response: Dict[str, Any]
    ) -> None:
        """Test parsing non-streaming response with tool use."""
        result = await anthropic_provider._parse_non_streaming_response(tool_use_invoke_model_response)

        assert isinstance(result, NonStreamingResponse)
        assert result.type == LLMCallResponseTypes.NON_STREAMING
        assert len(result.content) == 2

        # Check text block
        text_block = result.content[0]
        assert isinstance(text_block, TextBlockData)
        assert text_block.content.text == "I'll help you search for that information."

        # Check tool use block
        tool_block = result.content[1]
        assert isinstance(tool_block, ToolUseRequestData)
        assert tool_block.type == ContentBlockCategory.TOOL_USE_REQUEST
        assert isinstance(tool_block.content, ToolUseRequestContent)
        assert tool_block.content.tool_name == "search_web"
        assert tool_block.content.tool_use_id == "toolu_123"
        assert tool_block.content.tool_input == {"query": "python programming"}

        # Check usage with cache tokens
        assert result.usage.input == 25
        assert result.usage.output == 45
        assert result.usage.cache_read == 10
        assert result.usage.cache_write == 5


class TestAnthropicServiceClientIntegration:
    """Test suite for call_service_client method."""

    @pytest.mark.asyncio
    async def test_call_service_client_non_streaming(
        self,
        anthropic_provider: Anthropic,
        sample_invoke_model_response: Dict[str, Any],
        sample_model_config: Dict[str, Any],
    ) -> None:
        """Test call_service_client for non-streaming responses."""
        with patch.object(anthropic_provider, "_get_model_config", return_value=sample_model_config):
            with patch.object(anthropic_provider, "_get_service_client_and_model_name") as mock_get_client:
                mock_client = MagicMock()
                mock_client.get_llm_non_stream_response = AsyncMock(return_value=sample_invoke_model_response)
                mock_get_client.return_value = (mock_client, "test-model-id")

                llm_payload = {"test": "payload"}
                session_id = 123

                result = await anthropic_provider.call_service_client(
                    session_id=session_id, llm_payload=llm_payload, model=LLModels.CLAUDE_3_POINT_5_SONNET, stream=False
                )

                # Verify service client was called correctly
                mock_get_client.assert_called_once_with(
                    session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
                )
                mock_client.get_llm_non_stream_response.assert_called_once_with(
                    llm_payload=llm_payload, model="test-model-id"
                )

                # Verify result is properly parsed
                assert isinstance(result, NonStreamingResponse)
                assert result.type == LLMCallResponseTypes.NON_STREAMING

    @pytest.mark.asyncio
    async def test_call_service_client_streaming(
        self,
        anthropic_provider: Anthropic,
        mock_streaming_response: MagicMock,
        mock_async_bedrock_client: MagicMock,
        sample_model_config: Dict[str, Any],
    ) -> None:
        """Test call_service_client for streaming responses."""
        with patch.object(anthropic_provider, "_get_model_config", return_value=sample_model_config):
            with patch.object(anthropic_provider, "_get_service_client_and_model_name") as mock_get_client:
                mock_client = MagicMock()
                mock_client.get_llm_stream_response = AsyncMock(
                    return_value=(mock_streaming_response, mock_async_bedrock_client)
                )
                mock_get_client.return_value = (mock_client, "test-model-id")

                # Mock the _parse_streaming_response method
                mock_streaming_result = MagicMock(spec=StreamingResponse)
                mock_streaming_result.type = LLMCallResponseTypes.STREAMING

                with patch.object(anthropic_provider, "_parse_streaming_response", return_value=mock_streaming_result):
                    llm_payload = {"test": "payload"}
                    session_id = 456

                    result = await anthropic_provider.call_service_client(
                        session_id=session_id,
                        llm_payload=llm_payload,
                        model=LLModels.CLAUDE_3_POINT_5_SONNET,
                        stream=True,
                    )

                    # Verify service client was called correctly
                    mock_get_client.assert_called_once_with(
                        session_id, LLModels.CLAUDE_3_POINT_5_SONNET, sample_model_config
                    )
                    mock_client.get_llm_stream_response.assert_called_once_with(
                        llm_payload=llm_payload, model="test-model-id"
                    )

                    # Verify result is streaming response
                    assert result.type == LLMCallResponseTypes.STREAMING


class TestAnthropicTokenCounting:
    """Test suite for token counting methods."""

    @pytest.mark.asyncio
    async def test_get_tokens(self, anthropic_provider: Anthropic, mock_tiktoken_client: MagicMock) -> None:
        """Test get_tokens method."""
        with patch(
            "deputydev_core.llm_handler.providers.anthropic.llm_provider.TikToken",
            return_value=mock_tiktoken_client,
        ):
            content = "Hello, how are you doing today?"
            result = await anthropic_provider.get_tokens(content, LLModels.CLAUDE_3_POINT_5_SONNET)

            mock_tiktoken_client.count.assert_called_once_with(text=content)
            assert result == 42

    def test_extract_payload_content_for_token_counting_basic(
        self, anthropic_provider: Anthropic, sample_llm_payload_for_token_counting: Dict[str, Any]
    ) -> None:
        """Test payload content extraction for token counting."""
        result = anthropic_provider._extract_payload_content_for_token_counting(sample_llm_payload_for_token_counting)

        expected_parts = [
            "You are a helpful assistant.",  # system message
            "Hello, how are you?",  # user message text
            "I'm doing well, thank you!",  # assistant message text
        ]

        for part in expected_parts:
            assert part in result

        # Should also contain tools information
        assert "search_web" in result
        assert "Search the web for information" in result

    def test_extract_payload_content_for_token_counting_complex_system(
        self, anthropic_provider: Anthropic, complex_llm_payload_for_token_counting: Dict[str, Any]
    ) -> None:
        """Test payload content extraction with complex system message."""
        result = anthropic_provider._extract_payload_content_for_token_counting(complex_llm_payload_for_token_counting)

        # Should handle system message as array
        assert "You are a helpful assistant with access to tools." in result

        # Should handle tool_result content
        assert "Some tool output" in result

        # Should handle tools
        assert "file_processor" in result
        assert "Process files" in result

    def test_extract_payload_content_for_token_counting_malformed(
        self, anthropic_provider: Anthropic, malformed_llm_payload_for_token_counting: Dict[str, Any]
    ) -> None:
        """Test payload content extraction with malformed data."""
        result = anthropic_provider._extract_payload_content_for_token_counting(
            malformed_llm_payload_for_token_counting
        )

        # Should return error message instead of crashing
        # The method handles errors gracefully and returns either empty string or error message
        assert isinstance(result, str)
        # Could be empty string or error message depending on the implementation
        assert result in ["", "Unable to extract content for token counting"]

    def test_extract_payload_content_for_token_counting_empty_payload(self, anthropic_provider: Anthropic) -> None:
        """Test payload content extraction with empty payload."""
        result = anthropic_provider._extract_payload_content_for_token_counting({})

        # Should handle empty payload gracefully
        assert isinstance(result, str)
        assert result == ""  # Empty string for empty payload

    def test_extract_payload_content_for_token_counting_no_messages(self, anthropic_provider: Anthropic) -> None:
        """Test payload content extraction with system only."""
        payload = {"system": "You are a helpful assistant."}

        result = anthropic_provider._extract_payload_content_for_token_counting(payload)

        assert "You are a helpful assistant." in result

    def test_extract_payload_content_for_token_counting_tools_serialization_error(
        self, anthropic_provider: Anthropic
    ) -> None:
        """Test payload content extraction when tools cannot be serialized."""

        # Create a payload with non-serializable tools
        class NonSerializable:
            pass

        payload = {
            "system": "Test system",
            "messages": [],
            "tools": [NonSerializable()],  # This will cause JSON serialization to fail
        }

        with patch("deputydev_core.llm_handler.providers.anthropic.llm_provider.AppLogger") as mock_logger:
            result = anthropic_provider._extract_payload_content_for_token_counting(payload)

            # Should still return system message and handle tools error gracefully
            assert "Test system" in result
            # Should log a warning about tools processing error
            mock_logger.log_warn.assert_called()


class TestAnthropicEdgeCases:
    """Test suite for edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_conversation_turn_conversion_empty_content(self, anthropic_provider: Anthropic) -> None:
        """Test conversation turn conversion with empty content lists."""
        from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import UserConversationTurn

        empty_user_turn = UserConversationTurn(content=[])
        result = anthropic_provider._get_anthropic_conversation_turn_from_user_conversation_turn(empty_user_turn)

        assert isinstance(result, ConversationTurn)
        assert result.role == ConversationRole.USER
        assert len(result.content) == 0

    @pytest.mark.asyncio
    async def test_region_selection_with_single_region(self, anthropic_provider: Anthropic) -> None:
        """Test region selection when only one region is available."""
        single_region_config = {
            "PROVIDER_CONFIG": {
                "REGION_AND_IDENTIFIER_LIST": [
                    {"AWS_REGION": "us-east-1", "MODEL_IDENTIFIER": "anthropic.claude-3-sonnet-20240229-v1:0"}
                ]
            }
        }

        # Test multiple session IDs - all should return same region
        for session_id in [1, 2, 3, 100, 999]:
            region, model_id = await anthropic_provider._get_best_region_for_query(
                session_id, LLModels.CLAUDE_3_POINT_5_SONNET, single_region_config
            )
            assert region == "us-east-1"
            assert model_id == "anthropic.claude-3-sonnet-20240229-v1:0"

    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_empty_content(self, anthropic_provider: Anthropic) -> None:
        """Test parsing non-streaming response with empty content array."""
        body_content = {
            "content": [],
            "usage": {
                "input_tokens": 5,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        }

        mock_body = MagicMock()
        mock_body.read = AsyncMock(return_value=json.dumps(body_content).encode("utf-8"))

        response = {"body": mock_body, "ResponseMetadata": {"RequestId": "test"}}

        result = await anthropic_provider._parse_non_streaming_response(response)

        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 0
        assert result.usage.input == 5
        assert result.usage.output == 0

    def test_extract_payload_content_handles_none_values(self, anthropic_provider: Anthropic) -> None:
        """Test payload content extraction handles None values gracefully."""
        payload = {"system": None, "messages": None, "tools": None}

        result = anthropic_provider._extract_payload_content_for_token_counting(payload)

        # Should handle None values without crashing
        assert isinstance(result, str)
        # Result should be empty or contain error message depending on implementation
        # The actual implementation returns error message for None values
        assert result == "Unable to extract content for token counting" or len(result.strip()) == 0


class TestAnthropicParameterValidation:
    """Test suite for parameter validation and type safety."""

    @pytest.mark.asyncio
    async def test_get_conversation_turns_type_safety(
        self, anthropic_provider: Anthropic, sample_user_conversation_turn: UserConversationTurn
    ) -> None:
        """Test type safety in conversation turn conversion methods."""
        # Test that methods return correct types
        result = anthropic_provider._get_anthropic_conversation_turn_from_user_conversation_turn(
            sample_user_conversation_turn
        )

        assert isinstance(result, ConversationTurn)
        assert hasattr(result, "role")
        assert hasattr(result, "content")
        assert isinstance(result.content, list)

    @pytest.mark.asyncio
    async def test_region_query_return_types(
        self, anthropic_provider: Anthropic, sample_model_config: Dict[str, Any]
    ) -> None:
        """Test return types for region query methods."""
        region, model_id = await anthropic_provider._get_best_region_for_query(
            session_id=1, model_name=LLModels.CLAUDE_3_POINT_5_SONNET, model_config=sample_model_config
        )

        assert isinstance(region, str)
        assert isinstance(model_id, str)
        assert len(region) > 0
        assert len(model_id) > 0

    @pytest.mark.asyncio
    async def test_token_counting_return_type(
        self, anthropic_provider: Anthropic, mock_tiktoken_client: MagicMock
    ) -> None:
        """Test return type for get_tokens method."""
        with patch(
            "deputydev_core.llm_handler.providers.anthropic.llm_provider.TikToken",
            return_value=mock_tiktoken_client,
        ):
            result = await anthropic_provider.get_tokens("test content", LLModels.CLAUDE_3_POINT_5_SONNET)

            assert isinstance(result, int)
            assert result >= 0
