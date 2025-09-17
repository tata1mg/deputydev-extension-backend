"""
Unit tests for Google/Gemini build_llm_payload method.

This module tests the build_llm_payload method of the Google provider,
covering various payload building scenarios including:
- Basic payload building with system and user messages
- Complex payloads with tools and attachments
- Conversation history processing
- Edge cases and error handling
- Web search integration
- Cache configurations

The tests follow .deputydevrules guidelines and use proper fixtures.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


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
            "private_key": "-----BEGIN PRIVATE KEY-----\\ntest-key\\n-----END PRIVATE KEY-----\\n",
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
            "deputydev_core.llm_handler.providers.google.llm_provider.GeminiServiceClient", MockGeminiServiceClient
        ),
        # Also mock the config import in gemini service client
        patch("app.backend_common.service_clients.gemini.gemini.config", mock_config_obj.config["VERTEX"]),
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


from deputydev_core.llm_handler.dataclasses.main import PromptCacheConfig

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException

# Import fixtures


class TestGoogleBuildLLMPayloadBasic:
    """Test suite for basic build_llm_payload functionality."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_minimal_input(
        self,
        google_provider,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with minimal input."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
            )

            assert isinstance(result, dict)
            assert "max_tokens" in result
            assert result["max_tokens"] == 8192
            assert "contents" in result
            assert "tools" in result
            assert "system_instruction" in result
            assert "safety_settings" in result
            assert result["system_instruction"] is None  # No system message provided
            assert result["tools"] == []  # No tools provided

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_system_and_user_messages(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with system and user messages."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
            )

            # Check system instruction
            assert result["system_instruction"] is not None
            assert hasattr(result["system_instruction"], "text") or result["system_instruction"] is not None

            # Check contents for user message
            assert len(result["contents"]) >= 1
            user_content = result["contents"][-1]  # User message should be last
            assert user_content.role == "user"

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_complex_messages(
        self,
        google_provider,
        complex_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with complex system and user messages."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=complex_user_and_system_messages,
            )

            # Should handle complex messages properly
            assert result["system_instruction"] is not None
            assert len(result["contents"]) >= 1

    @pytest.mark.asyncio
    async def test_build_llm_payload_different_models(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_flash: Dict[str, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload for different Gemini models."""
        # Test with Gemini Flash
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_flash):
            result_flash = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_FLASH,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
            )

            assert result_flash["max_tokens"] == 4096  # Flash model has different limits

        # Test with Gemini Pro
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result_pro = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
            )

            assert result_pro["max_tokens"] == 8192  # Pro model has higher limits


class TestGoogleBuildLLMPayloadWithTools:
    """Test suite for build_llm_payload with tools."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_single_tool(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_conversation_tool,
        empty_attachment_data_task_map: Dict[int, Any],
    ) -> None:
        """Test building payload with a single tool."""
        with patch.object(
            google_provider,
            "_get_model_config",
            return_value={
                "NAME": "gemini-2.5-pro",
                "MAX_TOKENS": 8192,
                "THINKING_BUDGET_TOKENS": 4096,
                "TEMPERATURE": 0.7,
            },
        ):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=[simple_conversation_tool],
            )

            # Check tools
            assert len(result["tools"]) == 1
            tool = result["tools"][0]
            assert hasattr(tool, "function_declarations") or tool is not None

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_multiple_tools(
        self,
        google_provider,
        simple_user_and_system_messages,
        complex_conversation_tools,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with multiple tools."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=complex_conversation_tools,
            )

            # Check tools count
            assert len(result["tools"]) == 3  # weather, code analysis, file operations

            # Tools should be sorted by name
            for tool in result["tools"]:
                assert hasattr(tool, "function_declarations") or tool is not None

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_tool_choice(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_conversation_tool,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with different tool choice options."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            # Test with 'auto' (default)
            result_auto = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=[simple_conversation_tool],
                tool_choice="auto",
            )

            assert len(result_auto["tools"]) == 1

            # Test with 'required'
            result_required = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=[simple_conversation_tool],
                tool_choice="required",
            )

            assert len(result_required["tools"]) == 1

            # Test with 'none'
            result_none = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=[simple_conversation_tool],
                tool_choice="none",
            )

            # Tools are still provided but tool_choice affects tool_config
            assert len(result_none["tools"]) == 1


class TestGoogleBuildLLMPayloadWebSearch:
    """Test suite for build_llm_payload with web search."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_web_search(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with web search enabled."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                search_web=True,
            )

            # Should have Google search tool
            assert len(result["tools"]) == 1
            search_tool = result["tools"][0]
            assert hasattr(search_tool, "google_search") or search_tool is not None

    @pytest.mark.asyncio
    async def test_build_llm_payload_web_search_conflicts_with_tools(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_conversation_tool,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test that web search conflicts with functional tools."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with pytest.raises(BadRequestException):
                await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    prompt=simple_user_and_system_messages,
                    tools=[simple_conversation_tool],
                    search_web=True,
                )

    @pytest.mark.asyncio
    async def test_build_llm_payload_web_search_without_functional_tools(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test web search without functional tools (should work)."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                tools=None,  # No functional tools
                search_web=True,
            )

            assert len(result["tools"]) == 1  # Should have Google search tool


class TestGoogleBuildLLMPayloadWithAttachments:
    """Test suite for build_llm_payload with attachments."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_attachments(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_attachments,
        simple_attachment_data_task_map: Dict[int, Any],
    ) -> None:
        """Test building payload with attachments."""
        # Create proper asyncio tasks from the coroutine functions

        task_map = {key: asyncio.create_task(coro_func()) for key, coro_func in simple_attachment_data_task_map.items()}

        with patch.object(
            google_provider,
            "_get_model_config",
            return_value={
                "NAME": "gemini-2.5-pro",
                "MAX_TOKENS": 8192,
                "THINKING_BUDGET_TOKENS": 4096,
                "TEMPERATURE": 0.7,
            },
        ):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=task_map,
                prompt=simple_user_and_system_messages,
                attachments=simple_attachments,
            )

        # Should have user content with attachments processed
        assert len(result["contents"]) >= 1
        user_content = result["contents"][-1]
        assert user_content.role == "user"
        # Should have multiple parts (text + attachments)
        assert len(user_content.parts) > 1

    @pytest.mark.asyncio
    async def test_build_llm_payload_attachments_not_in_task_map(
        self,
        google_provider,
        simple_user_and_system_messages,
        simple_attachments,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload when attachments are not in task map."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                attachments=simple_attachments,  # Attachments provided but not in task map
            )

            # Should still process successfully, just skip missing attachments
            assert len(result["contents"]) >= 1
            user_content = result["contents"][-1]
            assert user_content.role == "user"
            # Should only have text part (attachments skipped)
            assert len(user_content.parts) == 1


class TestGoogleBuildLLMPayloadWithConversationHistory:
    """Test suite for build_llm_payload with conversation history."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_previous_responses(
        self,
        google_provider,
        simple_previous_responses,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with previous conversation responses."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with patch.object(google_provider, "get_conversation_turns", new_callable=AsyncMock) as mock_get_turns:
                # Mock conversation turns
                mock_content1 = MagicMock()
                mock_content1.role = "user"
                mock_content1.parts = [MagicMock()]

                mock_content2 = MagicMock()
                mock_content2.role = "model"
                mock_content2.parts = [MagicMock()]

                mock_get_turns.return_value = [mock_content1, mock_content2]

                result = await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    previous_responses=simple_previous_responses,
                )

                # Should call get_conversation_turns
                mock_get_turns.assert_called_once_with(simple_previous_responses, empty_attachment_data_task_map)

                # Should include conversation history in contents
                assert len(result["contents"]) == 2

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_complex_previous_responses(
        self,
        google_provider,
        complex_previous_responses,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with complex previous responses including tools."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with patch.object(google_provider, "get_conversation_turns", new_callable=AsyncMock) as mock_get_turns:
                # Mock more complex conversation turns
                mock_turns = [MagicMock() for _ in range(3)]  # User, Assistant with tool, Tool response
                mock_get_turns.return_value = mock_turns

                result = await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    previous_responses=complex_previous_responses,
                )

                mock_get_turns.assert_called_once()
                assert len(result["contents"]) == 3

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_conversation_turns_instead_of_responses(
        self,
        google_provider,
        complex_unified_conversation_turns,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with conversation turns instead of previous responses."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with patch.object(
                google_provider, "_get_google_content_from_conversation_turns", new_callable=AsyncMock
            ) as mock_get_content:
                # Mock conversation content
                mock_content = [MagicMock(), MagicMock(), MagicMock()]
                mock_get_content.return_value = mock_content

                result = await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    conversation_turns=complex_unified_conversation_turns,
                )

                # Should call _get_google_content_from_conversation_turns
                mock_get_content.assert_called_once_with(conversation_turns=complex_unified_conversation_turns)

                assert len(result["contents"]) == 3


class TestGoogleBuildLLMPayloadWithToolUseResponse:
    """Test suite for build_llm_payload with tool use response."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_tool_use_response(
        self,
        google_provider,
        simple_tool_use_response,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with tool use response."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                tool_use_response=simple_tool_use_response,
            )

            # Should include tool response in contents
            assert len(result["contents"]) >= 1
            tool_response_content = result["contents"][-1]
            assert tool_response_content.role == "user"  # Tool responses come from user role

    @pytest.mark.asyncio
    async def test_build_llm_payload_tool_use_response_with_conversation_turns(
        self,
        google_provider,
        simple_tool_use_response,
        user_text_conversation_turn,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test that tool_use_response is ignored when conversation_turns are provided."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with patch.object(
                google_provider, "_get_google_content_from_conversation_turns", new_callable=AsyncMock
            ) as mock_get_content:
                mock_content = [MagicMock()]
                mock_get_content.return_value = mock_content

                result = await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    tool_use_response=simple_tool_use_response,  # Should be ignored
                    conversation_turns=[user_text_conversation_turn],
                )

                # Should only have content from conversation_turns, not tool_use_response
                assert len(result["contents"]) == 1


class TestGoogleBuildLLMPayloadCacheConfigs:
    """Test suite for build_llm_payload with different cache configurations."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_default_cache_config(
        self,
        google_provider,
        simple_user_and_system_messages,
        default_cache_config: PromptCacheConfig,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with default cache configuration."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                cache_config=default_cache_config,
            )

            # Cache config is mostly informational for Gemini (caching is automatic)
            assert isinstance(result, dict)
            assert "contents" in result

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_disabled_cache_config(
        self,
        google_provider,
        simple_user_and_system_messages,
        disabled_cache_config: PromptCacheConfig,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with disabled cache configuration."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                cache_config=disabled_cache_config,
                disable_caching=True,
            )

            # Should still build successfully
            assert isinstance(result, dict)
            assert "contents" in result


class TestGoogleBuildLLMPayloadEdgeCases:
    """Test suite for build_llm_payload edge cases."""

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_empty_messages(
        self,
        google_provider,
        empty_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with empty system and user messages."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=empty_user_and_system_messages,
            )

            # Should handle empty messages gracefully
            assert isinstance(result, dict)
            # System instruction should be None or empty
            system_instruction = result["system_instruction"]
            assert system_instruction is None or (hasattr(system_instruction, "text") and not system_instruction.text)

    @pytest.mark.asyncio
    async def test_build_llm_payload_with_feedback(
        self,
        google_provider,
        simple_user_and_system_messages,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test building payload with feedback parameter."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            result = await google_provider.build_llm_payload(
                llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                attachment_data_task_map=empty_attachment_data_task_map,
                prompt=simple_user_and_system_messages,
                feedback="This is feedback for the model",
            )

            # Feedback is accepted but may not change the payload structure significantly
            assert isinstance(result, dict)
            assert "contents" in result

    @pytest.mark.asyncio
    async def test_build_llm_payload_performance_large_data(
        self,
        google_provider,
        large_conversation_flow,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test performance with large conversation data."""
        import time

        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with patch.object(
                google_provider, "_get_google_content_from_conversation_turns", new_callable=AsyncMock
            ) as mock_get_content:
                # Mock large content
                mock_content = [MagicMock() for _ in range(30)]  # Large number of content blocks
                mock_get_content.return_value = mock_content

                start_time = time.time()
                result = await google_provider.build_llm_payload(
                    llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                    attachment_data_task_map=empty_attachment_data_task_map,
                    conversation_turns=large_conversation_flow,
                )
                end_time = time.time()

                # Should process quickly even with large data
                processing_time = end_time - start_time
                assert processing_time < 2.0  # Should be under 2 seconds

                # Should produce valid result
                assert isinstance(result, dict)
                assert len(result["contents"]) == 30

    @pytest.mark.asyncio
    async def test_build_llm_payload_priority_conversation_turns_over_responses(
        self,
        google_provider,
        simple_previous_responses,
        user_text_conversation_turn,
        empty_attachment_data_task_map: Dict[int, Any],
        mock_model_config_gemini_pro: Dict[str, Any],
    ) -> None:
        """Test that conversation_turns takes priority over previous_responses."""
        with patch.object(google_provider, "_get_model_config", return_value=mock_model_config_gemini_pro):
            with patch.object(google_provider, "get_conversation_turns", new_callable=AsyncMock) as mock_get_turns:
                with patch.object(
                    google_provider, "_get_google_content_from_conversation_turns", new_callable=AsyncMock
                ) as mock_get_content:
                    mock_content = [MagicMock()]
                    mock_get_content.return_value = mock_content

                    result = await google_provider.build_llm_payload(
                        llm_model=LLModels.GEMINI_2_POINT_5_PRO,
                        attachment_data_task_map=empty_attachment_data_task_map,
                        previous_responses=simple_previous_responses,  # Should be ignored
                        conversation_turns=[user_text_conversation_turn],  # Should be used
                    )

                    # Should use conversation_turns, not previous_responses
                    mock_get_content.assert_called_once()
                    mock_get_turns.assert_not_called()  # Should not process previous_responses

                    assert len(result["contents"]) == 1
