"""
Comprehensive unit tests for Google/Gemini get_conversation_turns function.

This module tests the get_conversation_turns method of the Google provider,
covering various conversation scenarios including:
- Simple text messages
- Tool use requests and responses
- File attachments
- Extended thinking content
- Mixed content types
- Edge cases and error handling

The tests follow the .deputydevrules guidelines and include fixtures directly within the test file.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import Mock, patch

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
        function_call = type("FunctionCall", (), {"name": name, "args": args})()
        return cls(function_call=function_call)

    @classmethod
    def from_function_response(cls, name: str, response: Any):
        function_response = type("FunctionResponse", (), {"name": name, "response": response})()
        return cls(function_response=function_response)

    @classmethod
    def from_bytes(cls, data: bytes, mime_type: str):
        inline_data = type("InlineData", (), {"data": data, "mime_type": mime_type})()
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
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "12345",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
            "location": "us-central1",
        },
        "REDIS_CACHE_HOSTS": {"genai": {"LABEL": "test-genai", "HOST": "localhost", "PORT": 6379}},
        "INTERSERVICE_TIMEOUT": 30,
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
        patch.dict(
            "sys.modules",
            {
                "google": mock_google,
                "google.genai": mock_genai,
                "google.oauth2": mock_oauth2,
                "google.oauth2.service_account": mock_service_account,
            },
        ),
        # Mock CONFIG
        patch("app.backend_common.utils.sanic_wrapper.CONFIG", mock_config_obj),
        # Mock the service client directly at the module level
        patch(
            "app.backend_common.services.llm.providers.google.llm_provider.GeminiServiceClient", MockGeminiServiceClient
        ),
        # Also mock the config import in gemini service client
        patch("app.backend_common.service_clients.gemini.gemini.config", mock_config_obj.config["VERTEX"]),
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


class TestGoogleGetConversationTurns:
    """Test cases for Google get_conversation_turns method."""

    @pytest.fixture
    def google_provider(self):
        """Create a Google provider instance for testing."""
        from app.backend_common.services.llm.providers.google.llm_provider import Google

        return Google()

    @pytest.fixture
    def simple_text_message(self) -> MessageThreadDTO:
        """Create a simple text message from user."""
        return MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="test_hash_1",
            message_data=[TextBlockData(content=TextBlockContent(text="Hello, how are you?"))],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def assistant_text_message(self) -> MessageThreadDTO:
        """Create a simple text response from assistant."""
        return MessageThreadDTO(
            id=2,
            session_id=123,
            actor=MessageThreadActor.ASSISTANT,
            query_id=1,
            message_type=MessageType.RESPONSE,
            conversation_chain=[1, 2],
            data_hash="test_hash_2",
            message_data=[TextBlockData(content=TextBlockContent(text="I'm doing well, thank you for asking!"))],
            prompt_type="assistant_response",
            prompt_category="general",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=LLMUsage(input=10, output=15),
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def tool_use_request_message(self) -> MessageThreadDTO:
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
                        tool_input={"query": "Python best practices"}, tool_name="search_tool", tool_use_id="tool_123"
                    )
                )
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=LLMUsage(input=20, output=5),
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def tool_use_response_message(self) -> MessageThreadDTO:
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
                        response={"results": ["Follow PEP 8", "Use type hints", "Write tests"]},
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def message_with_file_attachment(self) -> MessageThreadDTO:
        """Create a message with file attachment."""
        return MessageThreadDTO(
            id=5,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=3,
            message_type=MessageType.QUERY,
            conversation_chain=[1, 2, 3, 4, 5],
            data_hash="test_hash_5",
            message_data=[FileBlockData(content=FileContent(attachment_id=42))],
            prompt_type="user_query",
            prompt_category="file_upload",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=None,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def message_with_extended_thinking(self) -> MessageThreadDTO:
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
                        type="thinking", thinking="Let me think about this carefully...", signature="assistant_thinking"
                    )
                )
            ],
            prompt_type="assistant_response",
            prompt_category="thinking",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=LLMUsage(input=5, output=25),
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def mixed_content_message(self) -> MessageThreadDTO:
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
                TextBlockData(content=TextBlockContent(text="Here's what I found:")),
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"file_path": "/path/to/file.py"}, tool_name="read_file", tool_use_id="tool_456"
                    )
                ),
            ],
            prompt_type="assistant_response",
            prompt_category="mixed",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            usage=LLMUsage(input=15, output=10),
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def simple_conversation_history(
        self,
        simple_text_message: MessageThreadDTO,
        assistant_text_message: MessageThreadDTO,
    ) -> List[MessageThreadDTO]:
        """Create a simple conversation history with user and assistant messages."""
        return [simple_text_message, assistant_text_message]

    @pytest.fixture
    def mock_image_attachment_data(self) -> ChatAttachmentDataWithObjectBytes:
        """Create mock image attachment data."""
        return ChatAttachmentDataWithObjectBytes(
            attachment_metadata=ChatAttachmentsDTO(
                id=42,
                file_name="test_image.png",
                file_type="image/png",
                s3_key="test-bucket/test_image.png",
                status="uploaded",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            object_bytes=b"fake_image_data",
        )

    @pytest.fixture
    def attachment_data_task_map_empty(self) -> Dict[int, asyncio.Task]:
        """Create an empty attachment data task map."""
        return {}

    @pytest.fixture
    def attachment_data_task_map_with_image(
        self,
        mock_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> Dict[int, Any]:
        """Create attachment data task map with image."""

        async def get_image_data() -> ChatAttachmentDataWithObjectBytes:
            return mock_image_attachment_data

        return {42: get_image_data}

    # ================== TEST METHODS ==================

    @pytest.mark.asyncio
    async def test_empty_conversation_history(
        self,
        google_provider,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test get_conversation_turns with empty message history."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_single_user_text_message(
        self,
        google_provider,
        simple_text_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing single user text message."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[simple_text_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert result[0].role == "user"
        assert len(result[0].parts) == 1
        assert result[0].parts[0].text == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_single_assistant_text_message(
        self,
        google_provider,
        assistant_text_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing single assistant text message."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[assistant_text_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert result[0].role == "model"
        assert len(result[0].parts) == 1
        assert result[0].parts[0].text == "I'm doing well, thank you for asking!"

    @pytest.mark.asyncio
    async def test_simple_conversation_flow(
        self,
        google_provider,
        simple_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing simple back-and-forth conversation."""
        result = await google_provider.get_conversation_turns(
            previous_responses=simple_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 2
        assert result[0].role == "user"
        assert result[0].parts[0].text == "Hello, how are you?"
        assert result[1].role == "model"
        assert result[1].parts[0].text == "I'm doing well, thank you for asking!"

    @pytest.mark.asyncio
    async def test_tool_use_request_processing(
        self,
        google_provider,
        tool_use_request_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with tool use request."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[tool_use_request_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Tool requests should not appear in result until matched with responses
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_tool_use_request_and_response_matching(
        self,
        google_provider,
        tool_use_request_message: MessageThreadDTO,
        tool_use_response_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test matching tool use request with its response."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[tool_use_request_message, tool_use_response_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 2

        # First should be the model's function call
        function_call_content = result[0]
        assert function_call_content.role == "model"
        assert len(function_call_content.parts) == 1
        assert hasattr(function_call_content.parts[0], "function_call")
        assert function_call_content.parts[0].function_call.name == "search_tool"
        assert function_call_content.parts[0].function_call.args == {"query": "Python best practices"}

        # Second should be the user's function response
        function_response_content = result[1]
        assert function_response_content.role == "user"
        assert len(function_response_content.parts) == 1
        assert hasattr(function_response_content.parts[0], "function_response")
        assert function_response_content.parts[0].function_response.name == "search_tool"
        expected_response = {"results": ["Follow PEP 8", "Use type hints", "Write tests"]}
        assert function_response_content.parts[0].function_response.response == expected_response

    @pytest.mark.asyncio
    async def test_extended_thinking_content_ignored(
        self,
        google_provider,
        message_with_extended_thinking: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that extended thinking content is ignored."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[message_with_extended_thinking],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Extended thinking should be skipped
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_file_attachment_processing_image(
        self,
        google_provider,
        message_with_file_attachment: MessageThreadDTO,
        attachment_data_task_map_with_image: Dict[int, Any],
    ) -> None:
        """Test processing message with image file attachment."""
        # Create the actual asyncio task
        task_map = {42: asyncio.create_task(attachment_data_task_map_with_image[42]())}

        result = await google_provider.get_conversation_turns(
            previous_responses=[message_with_file_attachment],
            attachment_data_task_map=task_map,
        )

        assert len(result) == 1
        assert result[0].role == "user"
        assert len(result[0].parts) == 1

        # Google Gemini uses bytes data with mime_type
        part = result[0].parts[0]
        assert hasattr(part, "inline_data")
        assert part.inline_data.mime_type == "image/png"
        assert part.inline_data.data == b"fake_image_data"

    @pytest.mark.asyncio
    async def test_file_attachment_not_in_task_map(
        self,
        google_provider,
        message_with_file_attachment: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing file attachment not present in task map."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[message_with_file_attachment],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Missing attachments should be ignored
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_mixed_content_types_processing(
        self,
        google_provider,
        mixed_content_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with mixed content types."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[mixed_content_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should have text message only (tool request will be stored for later matching)
        assert len(result) == 1
        assert result[0].role == "model"
        assert len(result[0].parts) == 1
        assert result[0].parts[0].text == "Here's what I found:"

    @pytest.mark.asyncio
    async def test_role_mapping_consistency(
        self,
        google_provider,
        simple_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that actor roles are mapped correctly to conversation roles."""
        result = await google_provider.get_conversation_turns(
            previous_responses=simple_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Verify role mapping
        user_content = [content for content in result if content.role == "user"][0]
        model_content = [content for content in result if content.role == "model"][0]

        assert user_content.parts[0].text == "Hello, how are you?"
        assert model_content.parts[0].text == "I'm doing well, thank you for asking!"

    @pytest.mark.asyncio
    async def test_empty_message_data_handling(
        self,
        google_provider,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test handling messages with empty message_data."""
        empty_message = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_empty",
            message_data=[],  # Empty message data
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await google_provider.get_conversation_turns(
            previous_responses=[empty_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_return_type_consistency(
        self,
        google_provider,
        simple_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that return type is consistent with expected structure."""
        result = await google_provider.get_conversation_turns(
            previous_responses=simple_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert isinstance(result, list)
        for content in result:
            # Content will be a mock of google_genai_types.Content
            assert hasattr(content, "role")
            assert hasattr(content, "parts")
            assert content.role in ["user", "model"]
            assert isinstance(content.parts, list)
            assert len(content.parts) > 0

    @pytest.mark.asyncio
    async def test_data_sorting_text_blocks_first(
        self,
        google_provider,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that TextBlockData is sorted before tool-related data."""
        # Create message with tool request before text (should be reordered)
        mixed_order_message = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.ASSISTANT,
            message_type=MessageType.RESPONSE,
            conversation_chain=[1],
            data_hash="hash_mixed_order",
            message_data=[
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"query": "test"}, tool_name="test_tool", tool_use_id="tool_123"
                    )
                ),
                TextBlockData(content=TextBlockContent(text="This text should come first")),
            ],
            prompt_type="assistant_response",
            prompt_category="mixed",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await google_provider.get_conversation_turns(
            previous_responses=[mixed_order_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should have text part only (tool request stored for later matching)
        assert len(result) == 1
        assert result[0].role == "model"
        assert len(result[0].parts) == 1
        assert result[0].parts[0].text == "This text should come first"

    @pytest.mark.asyncio
    async def test_message_with_multiple_content_blocks(
        self,
        google_provider,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with multiple content blocks of same type."""
        # Create message with multiple text blocks
        multi_content_message = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_multi",
            message_data=[
                TextBlockData(content=TextBlockContent(text="First part")),
                TextBlockData(content=TextBlockContent(text="Second part")),
                TextBlockData(content=TextBlockContent(text="Third part")),
            ],
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.GEMINI_2_POINT_5_PRO,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await google_provider.get_conversation_turns(
            previous_responses=[multi_content_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should create a single conversation turn with multiple parts
        assert len(result) == 1
        assert result[0].role == "user"
        assert len(result[0].parts) == 3
        assert result[0].parts[0].text == "First part"
        assert result[0].parts[1].text == "Second part"
        assert result[0].parts[2].text == "Third part"

    @pytest.mark.asyncio
    async def test_google_specific_content_structure(
        self,
        google_provider,
        simple_text_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that the returned structure matches Google's Content format exactly."""
        result = await google_provider.get_conversation_turns(
            previous_responses=[simple_text_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 1
        content = result[0]

        # Verify it's a proper Google Content object (or our mock version)
        # Content will be a mock of google_genai_types.Content
        assert content.role == "user"
        assert isinstance(content.parts, list)
        assert len(content.parts) == 1

        part = content.parts[0]
        # Part will be a mock of google_genai_types.Part
        assert hasattr(part, "text") or hasattr(part, "function_call") or hasattr(part, "function_response")
        assert part.text == "Hello, how are you?"
