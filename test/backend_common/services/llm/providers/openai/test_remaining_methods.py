"""
Comprehensive unit tests for remaining OpenAI LLM Provider methods.

This module tests the methods that haven't been covered by other test files:
- _get_openai_response_item_param_from_user_conversation_turn
- _get_openai_response_item_param_from_assistant_conversation_turn  
- _get_openai_response_item_param_from_tool_conversation_turn
- _get_openai_response_input_params_from_conversation_turns
- _parse_non_streaming_response
- _parse_non_streaming_response_new
- call_service_client
- _parse_streaming_response
- get_tokens
- _extract_payload_content_for_token_counting

The tests follow .deputydevrules guidelines and use proper fixtures.
"""

import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI
from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    TextBlockData,
    ToolUseRequestData,
)
from app.backend_common.services.llm.dataclasses.main import (
    LLMCallResponseTypes,
    NonStreamingResponse,
    StreamingResponse,
)

# Import fixtures
from test.fixtures.openai import (
    openai_provider,
    user_text_conversation_turn,
    user_multimodal_conversation_turn,
    assistant_text_conversation_turn,
    assistant_with_tool_request_turn,
    tool_response_conversation_turn,
    multi_tool_response_conversation_turn,
    complex_unified_conversation_turns,
    empty_conversation_turns,
    single_user_turn,
    assistant_with_multiple_tools,
    conversation_with_edge_cases,
    large_conversation_flow,
    mock_openai_response,
    mock_openai_response_with_function_call,
    mock_openai_response_new_format,
    mock_openai_response_new_format_with_function,
    mock_openai_response_without_usage,
    mock_streaming_response,
    mock_llm_payload,
    mock_llm_payload_with_tools,
    mock_llm_payload_complex,
    sample_content_for_token_counting,
    empty_llm_payload,
    malformed_llm_payload,
)


class TestOpenAIUnifiedConversationTurns:
    """Test suite for OpenAI unified conversation turn processing methods."""
    
    # ===============================
    # USER CONVERSATION TURN TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_response_item_param_from_user_text_turn(
        self,
        openai_provider: OpenAI,
        user_text_conversation_turn,
    ) -> None:
        """Test conversion of user text conversation turn to OpenAI format."""
        result = openai_provider._get_openai_response_item_param_from_user_conversation_turn(
            user_text_conversation_turn
        )
        
        # The Message object can be accessed like a dictionary
        assert result['role'] == "user"
        assert len(result['content']) == 1
        assert result['content'][0]['type'] == "input_text"
        assert result['content'][0]['text'] == "What's the weather like today?"
    
    @pytest.mark.asyncio 
    async def test_get_response_item_param_from_user_multimodal_turn(
        self,
        openai_provider: OpenAI,
        user_multimodal_conversation_turn,
    ) -> None:
        """Test conversion of user multimodal conversation turn to OpenAI format."""
        result = openai_provider._get_openai_response_item_param_from_user_conversation_turn(
            user_multimodal_conversation_turn
        )
        
        assert result['role'] == "user"
        assert len(result['content']) == 2
        
        # Text content
        text_content = result['content'][0]
        assert text_content['type'] == "input_text"
        assert text_content['text'] == "What do you see in this image?"
        
        # Image content
        image_content = result['content'][1]
        assert image_content['type'] == "input_image"
        assert image_content['detail'] == "auto"
        assert image_content['file_id'] is None
        assert image_content['image_url'].startswith("data:image/png;base64,")
    
    # ===============================
    # ASSISTANT CONVERSATION TURN TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_response_item_param_from_assistant_text_turn(
        self,
        openai_provider: OpenAI,
        assistant_text_conversation_turn,
    ) -> None:
        """Test conversion of assistant text conversation turn to OpenAI format."""
        result = openai_provider._get_openai_response_item_param_from_assistant_conversation_turn(
            assistant_text_conversation_turn
        )
        
        assert len(result) == 1
        # Text content
        assert result[0]['role'] == "assistant"
        assert result[0]['content'] == "I can help you with that!"
    
    @pytest.mark.asyncio
    async def test_get_response_item_param_from_assistant_with_tool_request(
        self,
        openai_provider: OpenAI,
        assistant_with_tool_request_turn,
    ) -> None:
        """Test conversion of assistant turn with tool request to OpenAI format."""
        result = openai_provider._get_openai_response_item_param_from_assistant_conversation_turn(
            assistant_with_tool_request_turn
        )
        
        assert len(result) == 2
        
        # Text content
        text_msg = result[0]
        assert text_msg['role'] == "assistant"
        assert text_msg['content'] == "Let me check the weather for you."
        
        # Tool call
        tool_call = result[1]
        assert tool_call['type'] == "function_call"
        assert tool_call['call_id'] == "weather_123"
        assert tool_call['name'] == "get_weather"
        
        parsed_args = json.loads(tool_call['arguments'])
        assert parsed_args == {"location": "New York", "units": "celsius"}
    
    @pytest.mark.asyncio
    async def test_get_response_item_param_from_assistant_multiple_tools(
        self,
        openai_provider: OpenAI,
        assistant_with_multiple_tools,
    ) -> None:
        """Test conversion of assistant turn with multiple tool requests."""
        result = openai_provider._get_openai_response_item_param_from_assistant_conversation_turn(
            assistant_with_multiple_tools
        )
        
        assert len(result) == 4  # 1 text + 3 tool calls
        
        # Text content
        assert result[0]['role'] == "assistant"
        assert result[0]['content'] == "I'll help you with multiple tasks."
        
        # Tool calls
        tool_calls = result[1:]
        tool_names = [call['name'] for call in tool_calls]
        assert "search_web" in tool_names
        assert "get_weather" in tool_names
        assert "calendar_check" in tool_names
        
        for call in tool_calls:
            assert call['type'] == "function_call"
            assert call['call_id'] is not None
            assert call['arguments'] is not None
    
    # ===============================
    # TOOL CONVERSATION TURN TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_response_item_param_from_tool_turn(
        self,
        openai_provider: OpenAI,
        tool_response_conversation_turn,
    ) -> None:
        """Test conversion of tool conversation turn to OpenAI format."""
        result = openai_provider._get_openai_response_item_param_from_tool_conversation_turn(
            tool_response_conversation_turn
        )
        
        assert len(result) == 1
        
        tool_output = result[0]
        assert tool_output['type'] == "function_call_output"
        assert tool_output['call_id'] == "weather_123"
        
        parsed_output = json.loads(tool_output['output'])
        expected = {"temperature": "22°C", "condition": "sunny", "humidity": "65%"}
        assert parsed_output == expected
    
    @pytest.mark.asyncio
    async def test_get_response_item_param_from_multi_tool_turn(
        self,
        openai_provider: OpenAI,
        multi_tool_response_conversation_turn,
    ) -> None:
        """Test conversion of tool turn with multiple responses to OpenAI format."""
        result = openai_provider._get_openai_response_item_param_from_tool_conversation_turn(
            multi_tool_response_conversation_turn
        )
        
        assert len(result) == 2
        
        # First tool response
        tool1 = result[0]
        assert tool1['call_id'] == "weather_123"
        parsed_output1 = json.loads(tool1['output'])
        assert "temperature" in parsed_output1
        
        # Second tool response  
        tool2 = result[1]
        assert tool2['call_id'] == "news_456"
        parsed_output2 = json.loads(tool2['output'])
        assert "headlines" in parsed_output2
    
    # ===============================
    # UNIFIED CONVERSATION TURNS INTEGRATION TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_openai_response_input_params_empty_turns(
        self,
        openai_provider: OpenAI,
        empty_conversation_turns,
    ) -> None:
        """Test processing empty conversation turns."""
        result = await openai_provider._get_openai_response_input_params_from_conversation_turns(
            empty_conversation_turns
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_openai_response_input_params_single_user_turn(
        self,
        openai_provider: OpenAI,
        single_user_turn,
    ) -> None:
        """Test processing single user conversation turn."""
        result = await openai_provider._get_openai_response_input_params_from_conversation_turns(
            single_user_turn
        )
        
        assert len(result) == 1
        assert result[0]['role'] == "user"
        assert result[0]['content'][0]['text'] == "Hello!"
    
    @pytest.mark.asyncio
    async def test_get_openai_response_input_params_complex_conversation(
        self,
        openai_provider: OpenAI,
        complex_unified_conversation_turns,
    ) -> None:
        """Test processing complex conversation with all turn types."""
        result = await openai_provider._get_openai_response_input_params_from_conversation_turns(
            complex_unified_conversation_turns
        )
        
        # Should have user message + assistant messages + tool calls + tool outputs  
        assert len(result) >= 4
        
        # Check user message with multimodal content
        user_msg = None
        for item in result:
            if isinstance(item, dict) and 'role' in item and item['role'] == "user":
                user_msg = item
                break
        
        assert user_msg is not None
        assert len(user_msg['content']) == 2  # text + image
        assert user_msg['content'][0]['type'] == "input_text"
        assert user_msg['content'][1]['type'] == "input_image"
        
        # Check tool calls exist
        tool_calls = [item for item in result if isinstance(item, dict) and item.get('type') == "function_call"]
        assert len(tool_calls) >= 2
        
        # Check tool outputs exist
        tool_outputs = [item for item in result if isinstance(item, dict) and item.get('type') == "function_call_output"]
        assert len(tool_outputs) >= 2
    
    @pytest.mark.asyncio
    async def test_get_openai_response_input_params_edge_cases(
        self,
        openai_provider: OpenAI,
        conversation_with_edge_cases,
    ) -> None:
        """Test processing conversation turns with edge cases."""
        result = await openai_provider._get_openai_response_input_params_from_conversation_turns(
            conversation_with_edge_cases
        )
        
        # Should handle empty content gracefully
        assert isinstance(result, list)
        
        # Find user message with empty text
        user_msgs = [item for item in result if isinstance(item, dict) and item.get('role') == "user"]
        assert len(user_msgs) >= 1
        
        # Find tool output with complex data
        tool_outputs = [item for item in result if isinstance(item, dict) and item.get('type') == "function_call_output"]
        if tool_outputs:
            complex_output = json.loads(tool_outputs[0]['output'])
            assert "results" in complex_output
            assert "metadata" in complex_output
    
    @pytest.mark.asyncio
    async def test_get_openai_response_input_params_performance_large_conversation(
        self,
        openai_provider: OpenAI,
        large_conversation_flow,
    ) -> None:
        """Test performance with large conversation flow."""
        import time
        
        start_time = time.time()
        result = await openai_provider._get_openai_response_input_params_from_conversation_turns(
            large_conversation_flow
        )
        end_time = time.time()
        
        # Should process reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should be under 2 seconds
        
        # Should produce reasonable number of outputs
        assert len(result) > 0
        assert isinstance(result, list)


class TestOpenAIResponseParsing:
    """Test suite for OpenAI response parsing methods."""
    
    # ===============================
    # NON-STREAMING RESPONSE PARSING TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_message_only(
        self,
        openai_provider: OpenAI,
        mock_openai_response,
    ) -> None:
        """Test parsing non-streaming response with message only."""
        result = openai_provider._parse_non_streaming_response(mock_openai_response)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 1
        
        content_block = result.content[0]
        assert isinstance(content_block, TextBlockData)
        assert content_block.content.text == "Hello, I can help you with that!"
        
        # Check usage
        assert result.usage.input == 80  # 100 - 20 cached
        assert result.usage.output == 50
        assert result.usage.cache_read == 20
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_with_function_call(
        self,
        openai_provider: OpenAI,
        mock_openai_response_with_function_call,
    ) -> None:
        """Test parsing non-streaming response with function call."""
        result = openai_provider._parse_non_streaming_response(mock_openai_response_with_function_call)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 1
        
        content_block = result.content[0]
        assert isinstance(content_block, ToolUseRequestData)
        assert content_block.content.tool_name == "search_function"
        assert content_block.content.tool_use_id == "call_12345"
        assert content_block.content.tool_input == {"query": "test query", "limit": 10}
        
        # Check usage
        assert result.usage.input == 120  # 150 - 30 cached
        assert result.usage.output == 75
        assert result.usage.cache_read == 30
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_without_usage(
        self,
        openai_provider: OpenAI,
        mock_openai_response_without_usage,
    ) -> None:
        """Test parsing non-streaming response without usage information."""
        result = openai_provider._parse_non_streaming_response(mock_openai_response_without_usage)
        
        assert isinstance(result, NonStreamingResponse)
        assert result.usage.input == 0
        assert result.usage.output == 0
        # Cache read can be None when there's no usage information
        assert result.usage.cache_read in [0, None]
    
    # ===============================
    # NEW FORMAT RESPONSE PARSING TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_new_format_text(
        self,
        openai_provider: OpenAI,
        mock_openai_response_new_format,
    ) -> None:
        """Test parsing new format non-streaming response with text."""
        result = openai_provider._parse_non_streaming_response_new(mock_openai_response_new_format)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 1
        
        content_block = result.content[0]
        assert isinstance(content_block, TextBlockData)
        assert content_block.content.text == "This is the response text"
        
        # Check usage
        assert result.usage.input == 95  # 120 - 25 cached
        assert result.usage.output == 60
        assert result.usage.cache_read == 25
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_new_format_with_function(
        self,
        openai_provider: OpenAI,
        mock_openai_response_new_format_with_function,
    ) -> None:
        """Test parsing new format response with function call and parsed arguments."""
        result = openai_provider._parse_non_streaming_response_new(mock_openai_response_new_format_with_function)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 1
        
        content_block = result.content[0]
        assert isinstance(content_block, ToolUseRequestData)
        assert content_block.content.tool_name == "get_weather"
        assert content_block.content.tool_use_id == "call_weather_123"
        assert content_block.content.tool_input == {"location": "New York", "units": "celsius"}
        
        # Check usage
        assert result.usage.input == 160  # 200 - 40 cached
        assert result.usage.output == 100
        assert result.usage.cache_read == 40


class TestOpenAIServiceClientCalls:
    """Test suite for OpenAI service client integration."""
    
    # ===============================
    # SERVICE CLIENT CALL TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_call_service_client_non_streaming_text(
        self,
        openai_provider: OpenAI,
        mock_llm_payload: Dict[str, Any],
    ) -> None:
        """Test service client call for non-streaming text response."""
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.OpenAIServiceClient') as mock_client:
            # Mock the service client response
            mock_response = MagicMock()
            mock_response.output = [MagicMock(type="message")]
            mock_response.output[0].content = [MagicMock(type="output_text", text="Test response")]
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 50
            mock_response.usage.output_tokens = 25
            mock_response.usage.input_tokens_details = MagicMock(cached_tokens=10)
            
            mock_client_instance = mock_client.return_value
            mock_client_instance.get_llm_non_stream_response_api = AsyncMock(return_value=mock_response)
            
            result = await openai_provider.call_service_client(
                session_id=123,
                llm_payload=mock_llm_payload,
                model=LLModels.GPT_4O,
                stream=False,
                response_type="text"
            )
            
            # Verify service client was called correctly
            mock_client_instance.get_llm_non_stream_response_api.assert_called_once()
            call_args = mock_client_instance.get_llm_non_stream_response_api.call_args
            assert call_args[1]['conversation_messages'] == mock_llm_payload['conversation_messages']
            assert call_args[1]['instructions'] == mock_llm_payload['system_message']
            assert call_args[1]['tools'] == mock_llm_payload['tools']
            
            # Verify result
            assert isinstance(result, NonStreamingResponse)
    
    @pytest.mark.asyncio
    async def test_call_service_client_non_streaming_json(
        self,
        openai_provider: OpenAI,
        mock_llm_payload: Dict[str, Any],
    ) -> None:
        """Test service client call for non-streaming JSON response."""
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.OpenAIServiceClient') as mock_client:
            # Mock the service client response
            mock_response = MagicMock()
            mock_response.output = [MagicMock(type="message")]
            mock_response.output_text = "JSON response"
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_response.usage.input_tokens_details = MagicMock(cached_tokens=20)
            
            mock_client_instance = mock_client.return_value
            mock_client_instance.get_llm_non_stream_response = AsyncMock(return_value=mock_response)
            
            result = await openai_provider.call_service_client(
                session_id=123,
                llm_payload=mock_llm_payload,
                model=LLModels.GPT_4O,
                stream=False,
                response_type="json_object"
            )
            
            # Verify service client was called correctly
            mock_client_instance.get_llm_non_stream_response.assert_called_once()
            
            # Verify result
            assert isinstance(result, NonStreamingResponse)
    
    @pytest.mark.asyncio
    async def test_call_service_client_streaming(
        self,
        openai_provider: OpenAI,
        mock_llm_payload: Dict[str, Any],
        mock_streaming_response,
    ) -> None:
        """Test service client call for streaming response."""
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.OpenAIServiceClient') as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.get_llm_stream_response = AsyncMock(return_value=mock_streaming_response)
            
            result = await openai_provider.call_service_client(
                session_id=123,
                llm_payload=mock_llm_payload,
                model=LLModels.GPT_4O,
                stream=True
            )
            
            # Verify service client was called correctly
            mock_client_instance.get_llm_stream_response.assert_called_once()
            
            # Verify result
            assert isinstance(result, StreamingResponse)
            assert result.type == LLMCallResponseTypes.STREAMING
    
    @pytest.mark.asyncio
    async def test_call_service_client_default_response_type(
        self,
        openai_provider: OpenAI,
        mock_llm_payload: Dict[str, Any],
    ) -> None:
        """Test service client call with default response type."""
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.OpenAIServiceClient') as mock_client:
            mock_response = MagicMock()
            mock_response.output = [MagicMock(type="message")]
            mock_response.output[0].content = [MagicMock(type="output_text", text="Default response")]
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 30
            mock_response.usage.output_tokens = 15
            mock_response.usage.input_tokens_details = MagicMock(cached_tokens=5)
            
            mock_client_instance = mock_client.return_value
            mock_client_instance.get_llm_non_stream_response_api = AsyncMock(return_value=mock_response)
            
            # Call without response_type (should default to "text")
            result = await openai_provider.call_service_client(
                session_id=123,
                llm_payload=mock_llm_payload,
                model=LLModels.GPT_4O
            )
            
            # Should use the text API endpoint
            mock_client_instance.get_llm_non_stream_response_api.assert_called_once()
            assert isinstance(result, NonStreamingResponse)


class TestOpenAITokenCounting:
    """Test suite for OpenAI token counting methods."""
    
    # ===============================
    # TOKEN COUNTING TESTS  
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_tokens_simple_content(
        self,
        openai_provider: OpenAI,
        sample_content_for_token_counting: str,
    ) -> None:
        """Test token counting for simple text content."""
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.TikToken') as mock_tiktoken:
            mock_instance = mock_tiktoken.return_value
            mock_instance.count.return_value = 42
            
            result = await openai_provider.get_tokens(
                content=sample_content_for_token_counting,
                model=LLModels.GPT_4O
            )
            
            assert result == 42
            mock_instance.count.assert_called_once_with(text=sample_content_for_token_counting)
    
    @pytest.mark.asyncio
    async def test_get_tokens_empty_content(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test token counting for empty content."""
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.TikToken') as mock_tiktoken:
            mock_instance = mock_tiktoken.return_value
            mock_instance.count.return_value = 0
            
            result = await openai_provider.get_tokens(
                content="",
                model=LLModels.GPT_4O
            )
            
            assert result == 0
    
    # ===============================
    # PAYLOAD CONTENT EXTRACTION TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_for_token_counting_complex(
        self,
        openai_provider: OpenAI,
        mock_llm_payload_complex: Dict[str, Any],
    ) -> None:
        """Test extracting content from complex LLM payload for token counting."""
        result = openai_provider._extract_payload_content_for_token_counting(mock_llm_payload_complex)
        
        # Should include system message
        assert "You are a helpful coding assistant" in result
        
        # Should include user messages
        assert "How do I implement a binary search?" in result
        
        # Should include assistant messages
        assert "Here's a Python implementation" in result
        
        # Should include function call outputs
        assert "def binary_search" in result
        
        # Should include tools information
        assert "code_executor" in result
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_for_token_counting_empty(
        self,
        openai_provider: OpenAI,
        empty_llm_payload: Dict[str, Any],
    ) -> None:
        """Test extracting content from empty LLM payload."""
        result = openai_provider._extract_payload_content_for_token_counting(empty_llm_payload)
        
        # Should handle empty payload gracefully
        assert isinstance(result, str)
        # Empty payload should result in minimal content
        assert len(result.strip()) == 0 or result == ""
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_for_token_counting_malformed(
        self,
        openai_provider: OpenAI,
        malformed_llm_payload: Dict[str, Any],
    ) -> None:
        """Test extracting content from malformed LLM payload."""
        result = openai_provider._extract_payload_content_for_token_counting(malformed_llm_payload)
        
        # Should handle malformed payload gracefully and return fallback
        assert isinstance(result, str)
        # May return placeholder text for malformed payloads
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_handles_list_content(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test extracting content from payload with list-type content."""
        payload = {
            "system_message": "Test system",
            "conversation_messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "First text"},
                        {"type": "input_text", "text": "Second text"},
                        {"type": "input_image", "image_url": "data:image/png;base64,xyz"}  # Should be ignored
                    ]
                }
            ]
        }
        
        result = openai_provider._extract_payload_content_for_token_counting(payload)
        
        assert "Test system" in result
        assert "First text" in result  
        assert "Second text" in result
        # Image content should not be included
        assert "data:image" not in result
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_handles_tools_serialization_error(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test handling tools that can't be JSON serialized."""
        # Create a payload with non-serializable tools
        class NonSerializable:
            pass
        
        payload = {
            "system_message": "Test",
            "conversation_messages": [],
            "tools": [{"non_serializable": NonSerializable()}]
        }
        
        # Should handle serialization error gracefully
        result = openai_provider._extract_payload_content_for_token_counting(payload)
        
        assert isinstance(result, str)
        assert "Test" in result  # System message should still be included


class TestOpenAIStreamingResponseParsing:
    """Test suite for OpenAI streaming response parsing."""
    
    # ===============================
    # STREAMING RESPONSE PARSING TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_parse_streaming_response_basic(
        self,
        openai_provider: OpenAI,
        mock_streaming_response,
    ) -> None:
        """Test basic streaming response parsing."""
        result = await openai_provider._parse_streaming_response(
            mock_streaming_response,
            stream_id="test_stream_123",
            session_id=456
        )
        
        assert isinstance(result, StreamingResponse)
        assert result.type == LLMCallResponseTypes.STREAMING
        
        # Test the streaming content
        events = []
        async for event in result.content:
            events.append(event)
        
        # Should have text block start, deltas, end, but not completion event
        assert len(events) >= 3
        
        # Check usage after streaming completes
        usage = await result.usage
        assert usage.input == 80  # 100 - 20 cached
        assert usage.output == 50
        assert usage.cache_read == 20
        
        # Check accumulated events
        accumulated = await result.accumulated_events
        assert len(accumulated) >= 3
    
    @pytest.mark.asyncio
    async def test_parse_streaming_response_with_cancellation(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test streaming response with cancellation checker."""
        # Mock a cancellation checker
        mock_checker = MagicMock()
        mock_checker.is_cancelled.return_value = True
        mock_checker.stop_monitoring = AsyncMock()
        
        openai_provider.checker = mock_checker
        
        # Create a simple streaming response
        async def cancelled_stream():
            event = MagicMock()
            event.type = "response.output_text.delta"
            event.delta = "test"
            yield event
        
        # Mock the entire cache to avoid Redis issues
        with patch('app.backend_common.services.llm.providers.openai.llm_provider.CodeGenTasksCache') as mock_cache:
            mock_cache.cleanup_session_data = AsyncMock()
            
            result = await openai_provider._parse_streaming_response(
                cancelled_stream(),
                session_id=789
            )
            
            # Consume events - cancellation should be checked
            events = []
            try:
                async for event in result.content:
                    events.append(event)
            except asyncio.CancelledError:
                # This is expected when cancellation happens
                pass
            
            # Should have checked for cancellation
            mock_checker.is_cancelled.assert_called()
            
            # Wait for the usage to be available (needed for proper cleanup)
            usage = await result.usage
            assert usage is not None
    
    @pytest.mark.asyncio
    async def test_parse_streaming_response_error_handling(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test streaming response error handling."""
        # Create a streaming response that raises an error
        async def error_stream():
            yield MagicMock(type="response.output_text.delta", delta="test")
            raise Exception("Stream error")
        
        # Should handle errors gracefully
        result = await openai_provider._parse_streaming_response(error_stream())
        
        events = []
        async for event in result.content:
            events.append(event)
        
        # Should process at least one event before error
        assert len(events) >= 1
        
        # Usage should be available
        usage = await result.usage
        # Usage should be a valid object (even if default/empty)
        assert usage is not None
        assert hasattr(usage, 'input')
        assert hasattr(usage, 'output')


class TestOpenAIIntegrationEdgeCases:
    """Test suite for integration scenarios and edge cases."""
    
    # ===============================
    # INTEGRATION AND EDGE CASE TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_conversation_turn_processing_type_safety(
        self,
        openai_provider: OpenAI,
        complex_unified_conversation_turns,
    ) -> None:
        """Test type safety in conversation turn processing."""
        result = await openai_provider._get_openai_response_input_params_from_conversation_turns(
            complex_unified_conversation_turns
        )
        
        # Verify all results have proper types
        for item in result:
            if hasattr(item, 'role'):
                # Message type
                assert item.role in ["user", "assistant"]
                assert hasattr(item, 'content')
            elif hasattr(item, 'type'):
                # Tool call or output type
                assert item.type in ["function_call", "function_call_output"]
                assert hasattr(item, 'call_id')
    
    @pytest.mark.asyncio 
    async def test_response_parsing_with_mixed_output_types(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test response parsing with mixed output types."""
        # Create response with both message and function call
        mock_response = MagicMock()
        
        message_output = MagicMock()
        message_output.type = "message"
        
        function_output = MagicMock() 
        function_output.type = "function_call"
        function_output.arguments = '{"test": "value"}'
        function_output.name = "test_function"
        function_output.call_id = "call_mixed_123"
        
        mock_response.output = [message_output, function_output]
        mock_response.output_text = "Mixed response text"
        mock_response.usage = None
        
        result = openai_provider._parse_non_streaming_response(mock_response)
        
        # Should handle both output types
        assert len(result.content) == 2
        assert isinstance(result.content[0], TextBlockData)
        assert isinstance(result.content[1], ToolUseRequestData)
    
    @pytest.mark.asyncio
    async def test_large_payload_content_extraction_performance(
        self,
        openai_provider: OpenAI,
    ) -> None:
        """Test performance of content extraction with large payloads."""
        import time
        
        # Create a large payload
        large_payload = {
            "system_message": "Large system message " * 100,
            "conversation_messages": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": f"Message {i} " * 50}]
                } 
                for i in range(100)
            ],
            "tools": [
                {
                    "name": f"tool_{i}",
                    "description": f"Tool description {i} " * 20,
                    "parameters": {"type": "object", "properties": {f"param_{j}": {"type": "string"} for j in range(10)}}
                }
                for i in range(20)
            ]
        }
        
        start_time = time.time()
        result = openai_provider._extract_payload_content_for_token_counting(large_payload)
        end_time = time.time()
        
        # Should process quickly even with large payload
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should be under 1 second
        
        # Should extract content successfully
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Large system message" in result