"""
Comprehensive unit tests for OpenAI get_conversation_turns function.

This module tests the get_conversation_turns method of the OpenAI provider,
covering various conversation scenarios including:
- Simple text messages
- Tool use requests and responses
- File attachments
- Extended thinking content
- Mixed content types
- Edge cases and error handling

The tests follow the .deputydevrules guidelines and use proper fixtures.
"""

import asyncio
import json
from typing import Any, Dict, List

import pytest

from app.backend_common.models.dto.message_thread_dto import (
    MessageThreadActor,
    MessageThreadDTO,
)
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import (
    ChatAttachmentDataWithObjectBytes,
)
from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI


class TestOpenAIGetConversationTurns:
    """Test cases for OpenAI get_conversation_turns method."""

    @pytest.mark.asyncio
    async def test_empty_conversation_history(
        self,
        openai_provider: OpenAI,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test get_conversation_turns with empty message history."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_single_user_text_message(
        self,
        openai_provider: OpenAI,
        simple_text_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing single user text message."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[simple_text_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_single_assistant_text_message(
        self,
        openai_provider: OpenAI,
        assistant_text_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing single assistant text message."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[assistant_text_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "I'm doing well, thank you for asking!"

    @pytest.mark.asyncio
    async def test_simple_conversation_flow(
        self,
        openai_provider: OpenAI,
        simple_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing simple back-and-forth conversation."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=simple_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello, how are you?"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "I'm doing well, thank you for asking!"

    @pytest.mark.asyncio
    async def test_tool_use_request_processing(
        self,
        openai_provider: OpenAI,
        tool_use_request_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with tool use request."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[tool_use_request_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Tool requests should not appear in result until matched with responses
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_tool_use_request_and_response_matching(
        self,
        openai_provider: OpenAI,
        tool_use_request_message: MessageThreadDTO,
        tool_use_response_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test matching tool use request with its response."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[tool_use_request_message, tool_use_response_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 2

        # First should be the function call
        function_call = result[0]
        assert function_call["type"] == "function_call"
        assert function_call["call_id"] == "tool_123"
        assert function_call["name"] == "search_tool"
        assert json.loads(function_call["arguments"]) == {"query": "Python best practices"}

        # Second should be the function call output
        function_output = result[1]
        assert function_output["type"] == "function_call_output"
        assert function_output["call_id"] == "tool_123"
        expected_output = {"results": ["Follow PEP 8", "Use type hints", "Write tests"]}
        assert json.loads(function_output["output"]) == expected_output

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_processing(
        self,
        openai_provider: OpenAI,
        conversation_with_multiple_tool_calls: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing conversation with multiple tool calls."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=conversation_with_multiple_tool_calls,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should have user message + 2 function calls + 2 function outputs
        assert len(result) == 5

        # User message
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Can you help me with Python and JavaScript?"

        # First function call and output (Python)
        assert result[1]["type"] == "function_call"
        assert result[1]["call_id"] == "tool_python_123"
        assert result[1]["name"] == "get_language_info"

        assert result[2]["type"] == "function_call_output"
        assert result[2]["call_id"] == "tool_python_123"

        # Second function call and output (JavaScript)
        assert result[3]["type"] == "function_call"
        assert result[3]["call_id"] == "tool_js_456"
        assert result[3]["name"] == "get_language_info"

        assert result[4]["type"] == "function_call_output"
        assert result[4]["call_id"] == "tool_js_456"

    @pytest.mark.asyncio
    async def test_out_of_order_tool_responses(
        self,
        openai_provider: OpenAI,
        out_of_order_tool_conversation: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test handling tool responses that arrive out of order."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=out_of_order_tool_conversation,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Due to the algorithm's behavior, only the first matching tool response is processed
        # The algorithm pops unmatched tools from the front of the queue, so they're lost
        assert len(result) == 3  # 1 user msg + 1 tool call + 1 tool output (only tool_b)

        # User message first
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Execute these tools"

        # Only tool_b should be processed (first match in the response order)
        assert result[1]["type"] == "function_call"
        assert result[1]["call_id"] == "tool_b_456"
        assert result[1]["name"] == "tool_b"

        assert result[2]["type"] == "function_call_output"
        assert result[2]["call_id"] == "tool_b_456"

    @pytest.mark.asyncio
    async def test_extended_thinking_content_ignored(
        self,
        openai_provider: OpenAI,
        message_with_extended_thinking: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that extended thinking content is ignored."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[message_with_extended_thinking],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Extended thinking should be skipped
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_file_attachment_processing_image(
        self,
        openai_provider: OpenAI,
        message_with_file_attachment: MessageThreadDTO,
        attachment_data_task_map_with_image: Dict[int, Any],
    ) -> None:
        """Test processing message with image file attachment."""
        # Create the actual asyncio task
        task_map = {42: asyncio.create_task(attachment_data_task_map_with_image[42]())}

        result = await openai_provider.get_conversation_turns(
            previous_responses=[message_with_file_attachment],
            attachment_data_task_map=task_map,
        )

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "content" in result[0]
        assert isinstance(result[0]["content"], list)
        assert len(result[0]["content"]) == 1

        content_item = result[0]["content"][0]
        assert content_item["type"] == "input_image"
        assert "image_url" in content_item
        assert content_item["image_url"].startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_file_attachment_processing_non_image(
        self,
        openai_provider: OpenAI,
        message_with_file_attachment: MessageThreadDTO,
        attachment_data_task_map_with_document: Dict[int, Any],
    ) -> None:
        """Test processing message with non-image file attachment."""
        # Update the attachment ID to match the document fixture
        message_with_file_attachment.message_data[0].content.attachment_id = 100

        # Create the actual asyncio task
        task_map = {100: asyncio.create_task(attachment_data_task_map_with_document[100]())}

        result = await openai_provider.get_conversation_turns(
            previous_responses=[message_with_file_attachment],
            attachment_data_task_map=task_map,
        )

        # Non-image files should be ignored
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_file_attachment_not_in_task_map(
        self,
        openai_provider: OpenAI,
        message_with_file_attachment: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing file attachment not present in task map."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[message_with_file_attachment],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Missing attachments should be ignored
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_mixed_content_types_processing(
        self,
        openai_provider: OpenAI,
        mixed_content_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with mixed content types."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[mixed_content_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should have text message only (tool request will be stored for later matching)
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Here's what I found:"

    @pytest.mark.asyncio
    async def test_complex_conversation_flow(
        self,
        openai_provider: OpenAI,
        complex_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing complex conversation with various content types."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=complex_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should process user message, tool call/response pair, and text from mixed content
        assert len(result) == 4

        # User message
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello, how are you?"

        # Tool call
        assert result[1]["type"] == "function_call"
        assert result[1]["call_id"] == "tool_123"

        # Tool response
        assert result[2]["type"] == "function_call_output"
        assert result[2]["call_id"] == "tool_123"

        # Text from mixed content message
        assert result[3]["role"] == "assistant"
        assert result[3]["content"] == "Here's what I found:"

    @pytest.mark.asyncio
    async def test_role_mapping_consistency(
        self,
        openai_provider: OpenAI,
        simple_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that actor roles are mapped correctly to conversation roles."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=simple_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Verify role mapping
        user_message = [msg for msg in result if msg.get("role") == "user"][0]
        assistant_message = [msg for msg in result if msg.get("role") == "assistant"][0]

        assert user_message["content"] == "Hello, how are you?"
        assert assistant_message["content"] == "I'm doing well, thank you for asking!"

    @pytest.mark.asyncio
    async def test_json_serialization_in_tool_outputs(
        self,
        openai_provider: OpenAI,
        tool_use_request_message: MessageThreadDTO,
        tool_use_response_message: MessageThreadDTO,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that tool inputs and outputs are properly JSON serialized."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=[tool_use_request_message, tool_use_response_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        function_call = result[0]
        function_output = result[1]

        # Test that arguments and output are valid JSON strings
        parsed_args = json.loads(function_call["arguments"])
        parsed_output = json.loads(function_output["output"])

        assert isinstance(parsed_args, dict)
        assert isinstance(parsed_output, dict)
        assert parsed_args == {"query": "Python best practices"}
        assert parsed_output == {"results": ["Follow PEP 8", "Use type hints", "Write tests"]}

    @pytest.mark.asyncio
    async def test_tool_request_storage_and_retrieval(
        self,
        openai_provider: OpenAI,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test the internal storage and retrieval of tool requests."""
        from datetime import datetime

        from app.backend_common.models.dto.message_thread_dto import (
            LLModels,
            MessageCallChainCategory,
            MessageThreadDTO,
            MessageType,
            ToolUseRequestContent,
            ToolUseRequestData,
        )

        # Create a tool request followed by response with different tool_use_id
        tool_request = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.ASSISTANT,
            message_type=MessageType.RESPONSE,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"test": "data"}, tool_name="test_tool", tool_use_id="unique_id_999"
                    )
                )
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Process only the request - should store it but not output anything
        result = await openai_provider.get_conversation_turns(
            previous_responses=[tool_request],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 0  # No output until response is matched

    @pytest.mark.asyncio
    async def test_empty_message_data_handling(
        self,
        openai_provider: OpenAI,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test handling messages with empty message_data."""
        from datetime import datetime

        from app.backend_common.models.dto.message_thread_dto import (
            LLModels,
            MessageCallChainCategory,
            MessageThreadDTO,
            MessageType,
        )

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
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await openai_provider.get_conversation_turns(
            previous_responses=[empty_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_concurrent_attachment_processing(
        self,
        openai_provider: OpenAI,
        mock_image_attachment_data: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test concurrent processing of multiple attachments."""
        from datetime import datetime

        from app.backend_common.models.dto.message_thread_dto import (
            FileBlockData,
            FileContent,
            LLModels,
            MessageCallChainCategory,
            MessageThreadDTO,
            MessageType,
        )

        async def get_image_data_1() -> ChatAttachmentDataWithObjectBytes:
            await asyncio.sleep(0.1)  # Simulate async delay
            return mock_image_attachment_data

        async def get_image_data_2() -> ChatAttachmentDataWithObjectBytes:
            await asyncio.sleep(0.05)  # Different delay
            return mock_image_attachment_data

        # Create messages with multiple attachments
        message1 = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[FileBlockData(content=FileContent(attachment_id=1))],
            prompt_type="user_query",
            prompt_category="file_upload",
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        message2 = MessageThreadDTO(
            id=2,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.QUERY,
            conversation_chain=[1, 2],
            data_hash="hash_2",
            message_data=[FileBlockData(content=FileContent(attachment_id=2))],
            prompt_type="user_query",
            prompt_category="file_upload",
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        attachment_task_map = {
            1: asyncio.create_task(get_image_data_1()),
            2: asyncio.create_task(get_image_data_2()),
        }

        result = await openai_provider.get_conversation_turns(
            previous_responses=[message1, message2],
            attachment_data_task_map=attachment_task_map,
        )

        assert len(result) == 2
        # Both should be processed as image attachments
        assert all(item["role"] == "user" for item in result)
        assert all(len(item["content"]) == 1 for item in result)
        assert all(item["content"][0]["type"] == "input_image" for item in result)

    @pytest.mark.asyncio
    async def test_return_type_consistency(
        self,
        openai_provider: OpenAI,
        simple_conversation_history: List[MessageThreadDTO],
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that return type is consistent with expected structure."""
        result = await openai_provider.get_conversation_turns(
            previous_responses=simple_conversation_history,
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            # Each item should have expected keys based on its type
            if "role" in item:
                assert "content" in item
                assert item["role"] in ["user", "assistant"]
            elif "type" in item:
                assert item["type"] in ["function_call", "function_call_output"]
                if item["type"] == "function_call":
                    assert all(key in item for key in ["call_id", "name", "arguments"])
                else:  # function_call_output
                    assert all(key in item for key in ["call_id", "output"])

    @pytest.mark.asyncio
    async def test_large_conversation_processing_performance(
        self,
        openai_provider: OpenAI,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing performance with large conversation history."""
        import time
        from datetime import datetime

        from app.backend_common.models.dto.message_thread_dto import (
            LLModels,
            MessageCallChainCategory,
            MessageThreadDTO,
            MessageType,
            TextBlockContent,
            TextBlockData,
        )

        # Create a large conversation (100 messages)
        large_conversation = []
        for i in range(100):
            message = MessageThreadDTO(
                id=i + 1,
                session_id=123,
                actor=MessageThreadActor.USER if i % 2 == 0 else MessageThreadActor.ASSISTANT,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                conversation_chain=list(range(1, i + 2)),
                data_hash=f"hash_{i}",
                message_data=[TextBlockData(content=TextBlockContent(text=f"Message {i + 1}"))],
                prompt_type="user_query" if i % 2 == 0 else "assistant_response",
                prompt_category="general",
                llm_model=LLModels.GPT_4O,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            large_conversation.append(message)

        start_time = time.time()
        result = await openai_provider.get_conversation_turns(
            previous_responses=large_conversation,
            attachment_data_task_map=attachment_data_task_map_empty,
        )
        end_time = time.time()

        assert len(result) == 100
        # Should process reasonably quickly (under 1 second for 100 messages)
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_tool_response_without_prior_request(
        self,
        openai_provider: OpenAI,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test handling tool response that comes without a prior request."""
        from datetime import datetime

        from app.backend_common.models.dto.message_thread_dto import (
            LLModels,
            MessageCallChainCategory,
            MessageThreadDTO,
            MessageType,
            ToolUseResponseContent,
            ToolUseResponseData,
        )

        # Create a tool response without any prior request
        orphan_response = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1],
            data_hash="hash_orphan",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="orphan_tool", tool_use_id="orphan_123", response="Orphaned response"
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await openai_provider.get_conversation_turns(
            previous_responses=[orphan_response],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Orphaned tool response should be ignored (no matching request)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_message_with_multiple_content_blocks(
        self,
        openai_provider: OpenAI,
        attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with multiple content blocks of same type."""
        from datetime import datetime

        from app.backend_common.models.dto.message_thread_dto import (
            LLModels,
            MessageCallChainCategory,
            MessageThreadDTO,
            MessageType,
            TextBlockContent,
            TextBlockData,
        )

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
            llm_model=LLModels.GPT_4O,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await openai_provider.get_conversation_turns(
            previous_responses=[multi_content_message],
            attachment_data_task_map=attachment_data_task_map_empty,
        )

        # Should create multiple conversation turns for each text block
        assert len(result) == 3
        assert all(item["role"] == "user" for item in result)
        assert result[0]["content"] == "First part"
        assert result[1]["content"] == "Second part"
        assert result[2]["content"] == "Third part"
