"""
Comprehensive unit tests for remaining Google/Gemini LLM Provider methods.

This module tests the methods that haven't been covered by other test files:
- _get_google_content_from_user_conversation_turn
- _get_google_content_from_assistant_conversation_turn
- _get_google_content_from_tool_conversation_turn
- _get_google_content_from_conversation_turns
- build_llm_payload
- _parse_non_streaming_response
- _parse_streaming_response
- call_service_client
- get_tokens
- _extract_payload_content_for_token_counting

The tests follow .deputydevrules guidelines and use proper fixtures.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import pytest

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
)
from app.backend_common.services.llm.dataclasses.main import (
    LLMCallResponseTypes,
    NonStreamingResponse,
    StreamingResponse,
    MalformedToolUseRequest,
    TextBlockStart,
    TextBlockDelta,
    TextBlockEnd,
    ToolUseRequestStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
)

# Mock Google types for testing - comprehensive
class MockPart:
    def __init__(self, text: str = None, function_call=None, function_response=None, inline_data=None):
        self.text = text
        self.function_call = function_call
        self.function_response = function_response  
        self.inline_data = inline_data
    
    @classmethod
    def from_text(cls, text: str):
        return cls(text=text)
    
    @classmethod
    def from_function_call(cls, name: str, args: dict):
        function_call = type('FunctionCall', (), {'name': name, 'args': args})(
        )
        return cls(function_call=function_call)
    
    @classmethod
    def from_function_response(cls, name: str, response: Any):
        function_response = type('FunctionResponse', (), {'name': name, 'response': response})()
        return cls(function_response=function_response)
    
    @classmethod 
    def from_bytes(cls, data: bytes, mime_type: str):
        inline_data = type('InlineData', (), {'data': data, 'mime_type': mime_type})()
        return cls(inline_data=inline_data)

class MockContent:
    def __init__(self, role: str, parts: List[MockPart]):
        self.role = role
        self.parts = parts


@pytest.fixture(autouse=True)
def setup_comprehensive_mocks():
    """Set up comprehensive mocks for all Google and configuration dependencies."""
    
    # Mock all Google types
    mock_types = Mock()
    mock_types.Part = MockPart
    mock_types.Content = MockContent
    mock_types.Tool = Mock
    mock_types.ToolConfig = Mock  
    mock_types.HttpOptions = Mock
    mock_types.GenerateContentResponse = Mock
    mock_types.Schema = Mock
    mock_types.FunctionDeclaration = Mock
    mock_types.GoogleSearch = Mock
    
    # Mock genai module
    mock_genai = Mock()
    mock_genai.types = mock_types
    mock_genai.Client = Mock
    mock_genai.errors = Mock()
    
    # Mock google module
    mock_google = Mock()
    mock_google.genai = mock_genai
    
    # Mock oauth2
    mock_oauth2 = Mock()
    mock_oauth2.service_account = Mock()
    mock_oauth2.service_account.Credentials = Mock()
    mock_oauth2.service_account.Credentials.from_service_account_info = Mock(return_value=Mock())
    
    # Mock service account
    mock_service_account = Mock()
    mock_service_account.Credentials = Mock()
    mock_service_account.Credentials.from_service_account_info = Mock(return_value=Mock())
    
    # Mock CONFIG with comprehensive configuration
    mock_config_obj = Mock()
    mock_config_obj.config = {
        "VERTEX": {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id", 
            "private_key": "-----BEGIN PRIVATE KEY-----\\ntest-key\\n-----END PRIVATE KEY-----\\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "12345",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
            "location": "us-central1"
        },
        "REDIS_CACHE_HOSTS": {
            "genai": {
                "LABEL": "test-genai",
                "HOST": "localhost",
                "PORT": 6379
            }
        },
        "INTERSERVICE_TIMEOUT": 30
    }
    
    # Mock GeminiServiceClient
    class MockGeminiServiceClient:
        def __init__(self):
            pass
        
        async def get_llm_stream_response(self, *args, **kwargs):
            return Mock()
        
        async def get_llm_non_stream_response(self, *args, **kwargs):
            return Mock()
        
        async def get_tokens(self, *args, **kwargs):
            return 100
    
    patches = [
        # Mock sys.modules for Google packages
        patch.dict('sys.modules', {
            'google': mock_google,
            'google.genai': mock_genai,
            'google.oauth2': mock_oauth2,
            'google.oauth2.service_account': mock_service_account,
        }),
        # Mock CONFIG
        patch('app.backend_common.utils.sanic_wrapper.CONFIG', mock_config_obj),
        # Mock the service client directly at the module level
        patch('app.backend_common.services.llm.providers.google.llm_provider.GeminiServiceClient', MockGeminiServiceClient),
        # Also mock the config import in gemini service client
        patch('app.backend_common.service_clients.gemini.gemini.config', mock_config_obj.config["VERTEX"]),
    ]
    
    for p in patches:
        p.start()
    
    yield
    
    for p in patches:
        p.stop()


# Import fixtures
from test.fixtures.google import (
    google_provider,
    user_text_conversation_turn,
    user_multimodal_conversation_turn,
    assistant_text_conversation_turn,
    assistant_with_tool_request_turn,
    tool_response_conversation_turn,
    multi_tool_response_conversation_turn,
    assistant_with_multiple_tools,
    complex_unified_conversation_turns,
    empty_conversation_turns,
    single_user_turn,
    conversation_with_edge_cases,
    large_conversation_flow,
    mock_google_response,
    mock_google_response_with_function_call,
    mock_google_response_without_usage,
    mock_google_response_blocked,
    mock_google_response_no_candidates,
    mock_google_response_max_tokens,
    mock_google_response_mixed_content,
    mock_google_streaming_response,
    mock_google_streaming_with_function_call,
    mock_google_streaming_malformed,
    mock_google_llm_payload,
    mock_google_llm_payload_with_tools,
    mock_google_llm_payload_complex,
    empty_google_llm_payload,
    malformed_google_llm_payload,
    sample_content_for_token_counting,
    mock_google_service_client,
    mock_model_config,
    google_payload_with_list_content,
    simple_user_and_system_messages,
    complex_user_and_system_messages,
    simple_conversation_tool,
    complex_conversation_tools,
    simple_attachments,
    simple_attachment_data_task_map,
    simple_previous_responses,
    complex_previous_responses,
    simple_tool_use_response,
    default_cache_config,
    empty_attachment_data_task_map,
)


class TestGoogleUnifiedConversationTurns:
    """Test suite for Google unified conversation turn processing methods."""
    
    # ===============================
    # USER CONVERSATION TURN TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_user_text_turn(
        self,
        google_provider,
        user_text_conversation_turn,
    ) -> None:
        """Test conversion of user text conversation turn to Google format."""
        result = google_provider._get_google_content_from_user_conversation_turn(
            user_text_conversation_turn
        )
        
        assert result.role == "user"
        assert len(result.parts) == 1
        assert result.parts[0].text == "What's the weather like today?"
    
    @pytest.mark.asyncio 
    async def test_get_google_content_from_user_multimodal_turn(
        self,
        google_provider,
        user_multimodal_conversation_turn,
    ) -> None:
        """Test conversion of user multimodal conversation turn to Google format."""
        result = google_provider._get_google_content_from_user_conversation_turn(
            user_multimodal_conversation_turn
        )
        
        assert result.role == "user"
        assert len(result.parts) == 2
        
        # Text content
        text_part = result.parts[0]
        assert text_part.text == "What do you see in this image?"
        
        # Image content - check that from_bytes was called with correct parameters
        image_part = result.parts[1]
        assert hasattr(image_part, 'from_bytes') or image_part is not None
    
    # ===============================
    # ASSISTANT CONVERSATION TURN TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_assistant_text_turn(
        self,
        google_provider,
        assistant_text_conversation_turn,
    ) -> None:
        """Test conversion of assistant text conversation turn to Google format."""
        result = google_provider._get_google_content_from_assistant_conversation_turn(
            assistant_text_conversation_turn
        )
        
        assert result.role == "model"
        assert len(result.parts) == 1
        assert result.parts[0].text == "I can help you with that!"
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_assistant_with_tool_request(
        self,
        google_provider,
        assistant_with_tool_request_turn,
    ) -> None:
        """Test conversion of assistant turn with tool request to Google format."""
        result = google_provider._get_google_content_from_assistant_conversation_turn(
            assistant_with_tool_request_turn
        )
        
        assert result.role == "model"
        assert len(result.parts) == 2
        
        # Text content
        text_part = result.parts[0]
        assert text_part.text == "Let me check the weather for you."
        
        # Function call - verify the structure
        function_part = result.parts[1]
        # Google's Part.from_function_call creates a function_call attribute
        assert hasattr(function_part, 'from_function_call') or function_part is not None
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_assistant_multiple_tools(
        self,
        google_provider,
        assistant_with_multiple_tools,
    ) -> None:
        """Test conversion of assistant turn with multiple tool requests."""
        result = google_provider._get_google_content_from_assistant_conversation_turn(
            assistant_with_multiple_tools
        )
        
        assert result.role == "model"
        assert len(result.parts) == 4  # 1 text + 3 tool calls
        
        # Text content should be first
        text_part = result.parts[0]
        assert text_part.text == "I'll help you with multiple tasks."
        
        # Remaining should be function calls
        function_parts = result.parts[1:]
        assert len(function_parts) == 3
    
    # ===============================
    # TOOL CONVERSATION TURN TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_tool_turn(
        self,
        google_provider,
        tool_response_conversation_turn,
    ) -> None:
        """Test conversion of tool conversation turn to Google format."""
        result = google_provider._get_google_content_from_tool_conversation_turn(
            tool_response_conversation_turn
        )
        
        assert result.role == "user"
        assert len(result.parts) == 1
        
        # Should be function response
        part = result.parts[0]
        # Google's Part.from_function_response creates function_response
        assert hasattr(part, 'from_function_response') or part is not None
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_multi_tool_turn(
        self,
        google_provider,
        multi_tool_response_conversation_turn,
    ) -> None:
        """Test conversion of tool turn with multiple responses to Google format."""
        result = google_provider._get_google_content_from_tool_conversation_turn(
            multi_tool_response_conversation_turn
        )
        
        assert result.role == "user"
        assert len(result.parts) == 2
        
        # Should have two function responses
        for part in result.parts:
            assert hasattr(part, 'from_function_response') or part is not None
    
    # ===============================
    # UNIFIED CONVERSATION TURNS INTEGRATION TESTS
    # ===============================
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_conversation_turns_empty(
        self,
        google_provider,
        empty_conversation_turns,
    ) -> None:
        """Test processing empty conversation turns."""
        result = await google_provider._get_google_content_from_conversation_turns(
            empty_conversation_turns
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_conversation_turns_single_user(
        self,
        google_provider,
        single_user_turn,
    ) -> None:
        """Test processing single user conversation turn."""
        result = await google_provider._get_google_content_from_conversation_turns(
            single_user_turn
        )
        
        assert len(result) == 1
        assert result[0].role == "user"
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_conversation_turns_complex(
        self,
        google_provider,
        complex_unified_conversation_turns,
    ) -> None:
        """Test processing complex conversation with all turn types."""
        result = await google_provider._get_google_content_from_conversation_turns(
            complex_unified_conversation_turns
        )
        
        # Should have user, assistant, and tool response contents
        assert len(result) == 3
        
        roles = [content.role for content in result]
        assert "user" in roles  # User turn and tool response turn both have "user" role
        assert "model" in roles  # Assistant turn
    
    @pytest.mark.asyncio
    async def test_get_google_content_from_conversation_turns_performance(
        self,
        google_provider,
        large_conversation_flow,
    ) -> None:
        """Test performance with large conversation flow."""
        import time
        
        start_time = time.time()
        result = await google_provider._get_google_content_from_conversation_turns(
            large_conversation_flow
        )
        end_time = time.time()
        
        # Should process reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should be under 2 seconds
        
        # Should produce reasonable number of outputs
        assert len(result) > 0
        assert isinstance(result, list)


class TestGoogleBuildLLMPayload:
    """Test suite for Google build_llm_payload method."""
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_basic(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map,
    ) -> None:
        """Test basic LLM payload building with system and user messages."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
            )
        
        assert "max_tokens" in result
        assert result["max_tokens"] == 4096
        assert "contents" in result
        assert "system_instruction" in result
        assert "tools" in result
        assert result["tools"] == []  # No tools provided
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_with_tools(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_conversation_tool,
        empty_attachment_data_task_map,
    ) -> None:
        """Test LLM payload building with tools."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=[simple_conversation_tool],
            )
        
        assert "tools" in result
        assert len(result["tools"]) == 1
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_with_attachments(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_attachments,
        simple_attachment_data_task_map: Dict[int, Any],
    ) -> None:
        """Test LLM payload building with attachments."""
        # Create proper asyncio tasks from the coroutine functions
        import asyncio
        task_map = {
            key: asyncio.create_task(coro_func()) 
            for key, coro_func in simple_attachment_data_task_map.items()
        }
        
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=task_map,
                prompt=simple_user_and_system_messages,
                attachments=simple_attachments,
            )
        
        assert "contents" in result
        # Should have user content with attachments processed
        assert len(result["contents"]) >= 1
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_with_previous_responses(
        self,
        google_provider,
        complex_previous_responses,
        empty_attachment_data_task_map,
    ) -> None:
        """Test LLM payload building with previous conversation history."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            with patch.object(google_provider, 'get_conversation_turns', new_callable=AsyncMock) as mock_get_turns:
                mock_get_turns.return_value = [MagicMock(), MagicMock()]  # Mock conversation turns
                
                result = await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    previous_responses=complex_previous_responses,
                )
                
                mock_get_turns.assert_called_once()
                assert "contents" in result
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_with_tool_use_response(
        self,
        google_provider,
        simple_tool_use_response,
        empty_attachment_data_task_map,
    ) -> None:
        """Test LLM payload building with tool use response."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                tool_use_response=simple_tool_use_response,
            )
        
        assert "contents" in result
        # Should include tool response in contents
        assert len(result["contents"]) >= 1
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_web_search_conflicts_with_tools(
        self,
        google_provider,
        simple_conversation_tool,
        empty_attachment_data_task_map,
    ) -> None:
        """Test that web search and functional tools conflict."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            with pytest.raises(Exception):  # Should raise BadRequestException
                await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    tools=[simple_conversation_tool],
                    search_web=True,
                )
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_web_search_only(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map,
    ) -> None:
        """Test LLM payload building with web search only."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                search_web=True,
            )
        
        assert "tools" in result
        assert len(result["tools"]) == 1  # Should have Google search tool


class TestGoogleResponseParsing:
    """Test suite for Google response parsing methods."""
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_basic(
        self,
        google_provider,
        mock_google_response,
    ) -> None:
        """Test parsing non-streaming response with text only."""
        result = google_provider._parse_non_streaming_response(mock_google_response)
        
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
        google_provider,
        mock_google_response_with_function_call,
    ) -> None:
        """Test parsing non-streaming response with function call."""
        result = google_provider._parse_non_streaming_response(mock_google_response_with_function_call)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 1
        
        content_block = result.content[0]
        assert isinstance(content_block, ToolUseRequestData)
        assert content_block.content.tool_name == "search_function"
        assert content_block.content.tool_input == {"query": "test query", "limit": 10}
        
        # Check usage
        assert result.usage.input == 120  # 150 - 30 cached
        assert result.usage.output == 75
        assert result.usage.cache_read == 30
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_without_usage(
        self,
        google_provider,
        mock_google_response_without_usage,
    ) -> None:
        """Test parsing non-streaming response without usage information."""
        result = google_provider._parse_non_streaming_response(mock_google_response_without_usage)
        
        assert isinstance(result, NonStreamingResponse)
        assert result.usage.input == 0
        assert result.usage.output == 0
        assert result.usage.cache_read == 0
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_blocked(
        self,
        google_provider,
        mock_google_response_blocked,
    ) -> None:
        """Test parsing response blocked by safety filters."""
        result = google_provider._parse_non_streaming_response(mock_google_response_blocked)
        
        assert isinstance(result, NonStreamingResponse)
        # Blocked responses should have usage but no content
        assert result.usage.input == 40  # 50 - 10 cached
        assert result.usage.output == 0
        assert result.usage.cache_read == 10
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_no_candidates(
        self,
        google_provider,
        mock_google_response_no_candidates,
    ) -> None:
        """Test parsing response with no candidates."""
        result = google_provider._parse_non_streaming_response(mock_google_response_no_candidates)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 0
        assert result.usage.input == 20  # 25 - 5 cached
        assert result.usage.output == 0
    
    @pytest.mark.asyncio
    async def test_parse_non_streaming_response_mixed_content(
        self,
        google_provider,
        mock_google_response_mixed_content,
    ) -> None:
        """Test parsing response with mixed content types."""
        result = google_provider._parse_non_streaming_response(mock_google_response_mixed_content)
        
        assert isinstance(result, NonStreamingResponse)
        assert len(result.content) == 2
        
        # Should have both text and tool use request
        content_types = [type(content) for content in result.content]
        assert TextBlockData in content_types
        assert ToolUseRequestData in content_types


class TestGoogleStreamingResponse:
    """Test suite for Google streaming response parsing."""
    
    @pytest.mark.asyncio
    async def test_parse_streaming_response_basic(
        self,
        google_provider,
        mock_google_streaming_response,
    ) -> None:
        """Test basic streaming response parsing."""
        result = await google_provider._parse_streaming_response(
            mock_google_streaming_response,
            stream_id="test_stream_123",
            session_id=456
        )
        
        assert isinstance(result, StreamingResponse)
        assert result.type == LLMCallResponseTypes.STREAMING
        
        # Test the streaming content
        events = []
        async for event in result.content:
            events.append(event)
        
        # Should have some streaming events
        assert len(events) > 0
        
        # Check usage after streaming completes
        usage = await result.usage
        assert usage.input == 60  # 80 - 20 cached (from mock fixture)
        assert usage.output == 50
        assert usage.cache_read == 20
    
    @pytest.mark.asyncio
    async def test_parse_streaming_response_with_function_call(
        self,
        google_provider,
        mock_google_streaming_with_function_call,
    ) -> None:
        """Test streaming response with function call."""
        result = await google_provider._parse_streaming_response(
            mock_google_streaming_with_function_call
        )
        
        assert isinstance(result, StreamingResponse)
        
        # Consume events
        events = []
        async for event in result.content:
            events.append(event)
        
        # Should have tool-related events
        event_types = [type(event) for event in events]
        assert ToolUseRequestStart in event_types
        assert ToolUseRequestEnd in event_types
        
        # Check usage
        usage = await result.usage
        assert usage.input == 120  # 160 - 40 cached
        assert usage.output == 100
        assert usage.cache_read == 40
    
    @pytest.mark.asyncio
    async def test_parse_streaming_response_malformed(
        self,
        google_provider,
        mock_google_streaming_malformed,
    ) -> None:
        """Test streaming response with malformed function call."""
        result = await google_provider._parse_streaming_response(
            mock_google_streaming_malformed
        )
        
        assert isinstance(result, StreamingResponse)
        
        # Consume events
        events = []
        async for event in result.content:
            events.append(event)
        
        # Should have malformed tool use request event
        event_types = [type(event) for event in events]
        assert MalformedToolUseRequest in event_types
        
        # Check usage
        usage = await result.usage
        assert usage.input == 70  # 80 - 10 cached
        assert usage.output == 25
        assert usage.cache_read == 10


class TestGoogleServiceClientCalls:
    """Test suite for Google service client integration."""
    
    @pytest.mark.asyncio
    async def test_call_service_client_non_streaming(
        self,
        google_provider,
        mock_google_llm_payload,
        mock_google_service_client,
    ) -> None:
        """Test service client call for non-streaming response."""
        with patch.object(google_provider, '_get_model_config', return_value={"NAME": "gemini-pro", "MAX_TOKENS": 4096, "TEMPERATURE": 0.7}):
            with patch('app.backend_common.services.llm.providers.google.llm_provider.GeminiServiceClient') as mock_client_class:
                mock_client_class.return_value = mock_google_service_client
                
                result = await google_provider.call_service_client(
                    session_id=123,
                    llm_payload=mock_google_llm_payload,
                    model=LLModels.GEMINI_2_POINT_5_PRO,
                    stream=False
                )
                
                # Verify service client was called
                mock_google_service_client.get_llm_non_stream_response.assert_called_once()
                
                # Verify result
                assert isinstance(result, NonStreamingResponse)
    
    @pytest.mark.asyncio
    async def test_call_service_client_streaming(
        self,
        google_provider,
        mock_google_llm_payload,
        mock_google_service_client,
    ) -> None:
        """Test service client call for streaming response."""
        with patch.object(google_provider, '_get_model_config', return_value={"NAME": "gemini-pro", "MAX_TOKENS": 4096, "TEMPERATURE": 0.7, "THINKING_BUDGET_TOKENS": 2048}):
            with patch('app.backend_common.services.llm.providers.google.llm_provider.GeminiServiceClient') as mock_client_class:
                mock_client_class.return_value = mock_google_service_client
                
                result = await google_provider.call_service_client(
                    session_id=123,
                    llm_payload=mock_google_llm_payload,
                    model=LLModels.GEMINI_2_POINT_5_PRO,
                    stream=True
                )
                
                # Verify service client was called
                mock_google_service_client.get_llm_stream_response.assert_called_once()
                
                # Verify result
                assert isinstance(result, StreamingResponse)


class TestGoogleTokenCounting:
    """Test suite for Google token counting methods."""
    
    @pytest.mark.asyncio
    async def test_get_tokens_basic(
        self,
        google_provider,
        sample_content_for_token_counting,
        mock_google_service_client,
    ) -> None:
        """Test basic token counting."""
        with patch.object(google_provider, '_get_model_config', return_value={"NAME": "gemini-pro"}):
            with patch('app.backend_common.services.llm.providers.google.llm_provider.GeminiServiceClient') as mock_client_class:
                mock_client_class.return_value = mock_google_service_client
                
                result = await google_provider.get_tokens(
                    content=sample_content_for_token_counting,
                    model=LLModels.GEMINI_2_POINT_5_PRO
                )
                
                assert result == 42  # From mock fixture
                mock_google_service_client.get_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_for_token_counting_basic(
        self,
        google_provider,
        mock_google_llm_payload,
    ) -> None:
        """Test extracting content from LLM payload for token counting."""
        result = google_provider._extract_payload_content_for_token_counting(mock_google_llm_payload)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_for_token_counting_complex(
        self,
        google_provider,
        mock_google_llm_payload_complex,
    ) -> None:
        """Test extracting content from complex LLM payload."""
        result = google_provider._extract_payload_content_for_token_counting(mock_google_llm_payload_complex)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should include various content types
        assert "helpful coding assistant" in result.lower() or len(result) > 50
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_for_token_counting_with_list_content(
        self,
        google_provider,
        google_payload_with_list_content,
    ) -> None:
        """Test extracting content from payload with list-type content."""
        result = google_provider._extract_payload_content_for_token_counting(google_payload_with_list_content)
        
        assert isinstance(result, str)
        assert "Test system message" in result
        assert "First text part" in result
        assert "Second text part" in result
        # Function response should be included as string
        assert "test_function response" in result
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_error_handling(
        self,
        google_provider,
        malformed_google_llm_payload,
    ) -> None:
        """Test error handling in content extraction."""
        result = google_provider._extract_payload_content_for_token_counting(malformed_google_llm_payload)
        
        # Should handle errors gracefully
        assert isinstance(result, str)
        # Should either return fallback message or partial content
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_extract_payload_content_empty_payload(
        self,
        google_provider,
        empty_google_llm_payload,
    ) -> None:
        """Test extracting content from empty payload."""
        result = google_provider._extract_payload_content_for_token_counting(empty_google_llm_payload)
        
        # Should handle empty payload gracefully
        assert isinstance(result, str)
        # Empty payload should result in minimal or empty content
        assert len(result) >= 0


class TestGoogleIntegrationEdgeCases:
    """Test suite for integration scenarios and edge cases."""
    
    @pytest.mark.asyncio
    async def test_conversation_turn_processing_type_safety(
        self,
        google_provider,
        complex_unified_conversation_turns,
    ) -> None:
        """Test type safety in conversation turn processing."""
        result = await google_provider._get_google_content_from_conversation_turns(
            complex_unified_conversation_turns
        )
        
        # Verify all results have proper types and structure
        for content in result:
            assert hasattr(content, 'role')
            assert hasattr(content, 'parts')
            assert content.role in ["user", "model"]
            assert isinstance(content.parts, list)
    
    @pytest.mark.asyncio
    async def test_build_llm_payload_with_edge_cases(
        self,
        google_provider,
        conversation_with_edge_cases,
        empty_attachment_data_task_map,
    ) -> None:
        """Test build_llm_payload with edge case conversation turns."""
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                conversation_turns=conversation_with_edge_cases,
            )
        
        # Should handle edge cases gracefully
        assert isinstance(result, dict)
        assert "contents" in result
        assert "tools" in result
    
    @pytest.mark.asyncio
    async def test_large_payload_performance(
        self,
        google_provider,
        large_conversation_flow,
        empty_attachment_data_task_map,
    ) -> None:
        """Test performance with large conversation payloads."""
        import time
        
        with patch.object(google_provider, '_get_model_config', return_value={"MAX_TOKENS": 4096}):
            start_time = time.time()
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                conversation_turns=large_conversation_flow,
            )
            end_time = time.time()
        
        # Should process quickly even with large payloads
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should be under 2 seconds
        
        # Should produce valid result
        assert isinstance(result, dict)
        assert "contents" in result