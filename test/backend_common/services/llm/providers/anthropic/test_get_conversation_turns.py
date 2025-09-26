"""
Comprehensive unit tests for Anthropic get_conversation_turns function.

This module tests the get_conversation_turns method of the Anthropic provider,
covering various conversation scenarios including:
- Simple text messages
- Tool use requests and responses
- File attachments (image handling)
- Extended thinking content (both thinking and redacted)
- Mixed content types
- Edge cases and error handling
- Anthropic-specific conversation turn formatting

The tests follow the .deputydevrules guidelines and use proper fixtures.
"""

import asyncio
import json
from typing import Any, Dict, List

import pytest
from deputydev_core.llm_handler.dataclasses.main import ConversationRole, ConversationTurn
from deputydev_core.llm_handler.providers.anthropic.llm_provider import Anthropic

from app.backend_common.models.dto.message_thread_dto import (
    MessageThreadActor,
    MessageThreadDTO,
)
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import (
    ChatAttachmentDataWithObjectBytes,
)


class TestAnthropicGetConversationTurns:
    """Test cases for Anthropic get_conversation_turns method."""

    @pytest.mark.asyncio
    async def test_empty_conversation_history(
        self,
        anthropic_provider: Anthropic,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test get_conversation_turns with empty message history."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_single_user_text_message(
        self,
        anthropic_provider: Anthropic,
        anthropic_simple_text_message: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing single user text message."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_simple_text_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert isinstance(result[0], ConversationTurn)
        assert result[0].role == ConversationRole.USER
        assert len(result[0].content) == 1
        assert result[0].content[0]["type"] == "text"
        assert result[0].content[0]["text"] == "Hello, how can you help me today?"

    @pytest.mark.asyncio
    async def test_single_assistant_text_message(
        self,
        anthropic_provider: Anthropic,
        anthropic_assistant_text_message: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing single assistant text message."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_assistant_text_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert isinstance(result[0], ConversationTurn)
        assert result[0].role == ConversationRole.ASSISTANT
        assert len(result[0].content) == 1
        assert result[0].content[0]["type"] == "text"
        assert result[0].content[0]["text"] == "I'd be happy to help you with anything you need!"

    @pytest.mark.asyncio
    async def test_simple_conversation_flow(
        self,
        anthropic_provider: Anthropic,
        anthropic_simple_conversation_history: List[MessageThreadDTO],
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing simple back-and-forth conversation."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=anthropic_simple_conversation_history,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 2

        # User message
        assert result[0].role == ConversationRole.USER
        assert result[0].content[0]["type"] == "text"
        assert result[0].content[0]["text"] == "Hello, how can you help me today?"

        # Assistant message
        assert result[1].role == ConversationRole.ASSISTANT
        assert result[1].content[0]["type"] == "text"
        assert result[1].content[0]["text"] == "I'd be happy to help you with anything you need!"

    @pytest.mark.asyncio
    async def test_tool_use_request_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_tool_use_request_message: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with tool use request only."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_tool_use_request_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Tool requests without responses should not appear in result
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_tool_use_request_and_response_matching(
        self,
        anthropic_provider: Anthropic,
        anthropic_tool_use_request_message: MessageThreadDTO,
        anthropic_tool_use_response_message: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test matching tool use request with its response."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_tool_use_request_message, anthropic_tool_use_response_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 2

        # First should be the assistant with tool use
        tool_call_turn = result[0]
        assert tool_call_turn.role == ConversationRole.ASSISTANT
        assert len(tool_call_turn.content) == 1
        assert tool_call_turn.content[0]["type"] == "tool_use"
        assert tool_call_turn.content[0]["name"] == "web_search"
        assert tool_call_turn.content[0]["id"] == "call_anthropic_123"
        assert tool_call_turn.content[0]["input"] == {"search_query": "Python code examples"}

        # Second should be the user with tool result
        tool_result_turn = result[1]
        assert tool_result_turn.role == ConversationRole.USER
        assert len(tool_result_turn.content) == 1
        assert tool_result_turn.content[0]["type"] == "tool_result"
        assert tool_result_turn.content[0]["tool_use_id"] == "call_anthropic_123"
        expected_response = {"results": ["Example 1: Hello World", "Example 2: Functions", "Example 3: Classes"]}
        assert json.loads(tool_result_turn.content[0]["content"]) == expected_response

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_conversation_with_multiple_tool_calls: List[MessageThreadDTO],
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing conversation with multiple tool calls."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=anthropic_conversation_with_multiple_tool_calls,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Should have user message + 2 assistant tool turns + 2 user result turns = 5 total
        assert len(result) == 5

        # User message
        assert result[0].role == ConversationRole.USER
        assert result[0].content[0]["text"] == "Can you analyze both Python and Ruby code?"

        # First tool use (Python)
        assert result[1].role == ConversationRole.ASSISTANT
        assert result[1].content[0]["type"] == "tool_use"
        assert result[1].content[0]["id"] == "call_py_123"
        assert result[1].content[0]["name"] == "code_analyzer"

        # First tool result (Python)
        assert result[2].role == ConversationRole.USER
        assert result[2].content[0]["type"] == "tool_result"
        assert result[2].content[0]["tool_use_id"] == "call_py_123"

        # Second tool use (Ruby)
        assert result[3].role == ConversationRole.ASSISTANT
        assert result[3].content[0]["type"] == "tool_use"
        assert result[3].content[0]["id"] == "call_rb_456"
        assert result[3].content[0]["name"] == "code_analyzer"

        # Second tool result (Ruby)
        assert result[4].role == ConversationRole.USER
        assert result[4].content[0]["type"] == "tool_result"
        assert result[4].content[0]["tool_use_id"] == "call_rb_456"

    @pytest.mark.asyncio
    async def test_out_of_order_tool_responses(
        self,
        anthropic_provider: Anthropic,
        anthropic_out_of_order_tool_conversation: List[MessageThreadDTO],
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test handling tool responses that arrive out of order."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=anthropic_out_of_order_tool_conversation,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Should process based on the order they appear in the response queue
        # The algorithm processes in order, so only the first matching response is processed
        assert len(result) == 3  # 1 user msg + 1 assistant tool + 1 user result (only first match)

        # User message first
        assert result[0].role == ConversationRole.USER
        assert result[0].content[0]["text"] == "Run these analysis tools"

        # Only first matched tool (call_beta_222) should be processed
        assert result[1].role == ConversationRole.ASSISTANT
        assert result[1].content[0]["type"] == "tool_use"
        assert result[1].content[0]["id"] == "call_beta_222"  # First matching response

        assert result[2].role == ConversationRole.USER
        assert result[2].content[0]["type"] == "tool_result"
        assert result[2].content[0]["tool_use_id"] == "call_beta_222"  # First in response order

    @pytest.mark.asyncio
    async def test_thinking_content_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_thinking_content: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that thinking content is properly processed."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_thinking_content],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert result[0].role == ConversationRole.ASSISTANT
        assert len(result[0].content) == 1
        assert result[0].content[0]["type"] == "thinking"
        assert result[0].content[0]["thinking"] == "Let me analyze this problem step by step..."
        assert result[0].content[0]["signature"] == "claude_thinking"

    @pytest.mark.asyncio
    async def test_redacted_thinking_content_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_redacted_thinking: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that redacted thinking content is properly processed."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_redacted_thinking],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 1
        assert result[0].role == ConversationRole.ASSISTANT
        assert len(result[0].content) == 1
        assert result[0].content[0]["type"] == "redacted_thinking"
        assert result[0].content[0]["data"] == "This content has been redacted"

    @pytest.mark.asyncio
    async def test_file_attachment_processing_image(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_file_attachment: MessageThreadDTO,
        anthropic_attachment_data_task_map_with_image: Dict[int, Any],
    ) -> None:
        """Test processing message with image file attachment."""
        # Create the actual asyncio task
        task_map = {50: asyncio.create_task(anthropic_attachment_data_task_map_with_image[50]())}

        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_file_attachment],
            attachment_data_task_map=task_map,
        )

        assert len(result) == 1
        assert result[0].role == ConversationRole.USER
        assert len(result[0].content) == 1

        content_item = result[0].content[0]
        assert content_item["type"] == "image"
        assert "source" in content_item
        assert content_item["source"]["type"] == "base64"
        assert content_item["source"]["media_type"] == "image/jpeg"
        assert "data" in content_item["source"]

    @pytest.mark.asyncio
    async def test_file_attachment_processing_non_image(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_file_attachment: MessageThreadDTO,
        anthropic_attachment_data_task_map_with_document: Dict[int, Any],
    ) -> None:
        """Test processing message with non-image file attachment."""
        # Update the attachment ID to match the document fixture
        anthropic_message_with_file_attachment.message_data[0].content.attachment_id = 200

        # Create the actual asyncio task
        task_map = {200: asyncio.create_task(anthropic_attachment_data_task_map_with_document[200]())}

        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_file_attachment],
            attachment_data_task_map=task_map,
        )

        # Non-image files should be ignored
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_file_attachment_not_in_task_map(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_file_attachment: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing file attachment not present in task map."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_file_attachment],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Missing attachments should be ignored
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_mixed_content_types_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_mixed_content_message: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with mixed content types."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_mixed_content_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Should have text message only (tool request will be stored for later matching)
        assert len(result) == 1
        assert result[0].role == ConversationRole.ASSISTANT
        assert len(result[0].content) == 1
        assert result[0].content[0]["type"] == "text"
        assert result[0].content[0]["text"] == "Let me search for that information:"

    @pytest.mark.asyncio
    async def test_complex_conversation_flow(
        self,
        anthropic_provider: Anthropic,
        anthropic_complex_conversation_history: List[MessageThreadDTO],
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing complex conversation with various content types."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=anthropic_complex_conversation_history,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Should process user message, tool call/response pair, and text from mixed content
        assert len(result) == 4

        # User message
        assert result[0].role == ConversationRole.USER
        assert result[0].content[0]["text"] == "Hello, how can you help me today?"

        # Tool use
        assert result[1].role == ConversationRole.ASSISTANT
        assert result[1].content[0]["type"] == "tool_use"
        assert result[1].content[0]["id"] == "call_anthropic_123"

        # Tool response
        assert result[2].role == ConversationRole.USER
        assert result[2].content[0]["type"] == "tool_result"
        assert result[2].content[0]["tool_use_id"] == "call_anthropic_123"

        # Text from mixed content message
        assert result[3].role == ConversationRole.ASSISTANT
        assert result[3].content[0]["text"] == "Let me search for that information:"

    @pytest.mark.asyncio
    async def test_role_mapping_consistency(
        self,
        anthropic_provider: Anthropic,
        anthropic_simple_conversation_history: List[MessageThreadDTO],
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that actor roles are mapped correctly to conversation roles."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=anthropic_simple_conversation_history,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Verify role mapping
        user_turn = [turn for turn in result if turn.role == ConversationRole.USER][0]
        assistant_turn = [turn for turn in result if turn.role == ConversationRole.ASSISTANT][0]

        assert user_turn.content[0]["text"] == "Hello, how can you help me today?"
        assert assistant_turn.content[0]["text"] == "I'd be happy to help you with anything you need!"

    @pytest.mark.asyncio
    async def test_json_serialization_in_tool_outputs(
        self,
        anthropic_provider: Anthropic,
        anthropic_tool_use_request_message: MessageThreadDTO,
        anthropic_tool_use_response_message: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that tool outputs are properly JSON serialized."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_tool_use_request_message, anthropic_tool_use_response_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        tool_use_turn = result[0]
        tool_result_turn = result[1]

        # Test that input is preserved as-is and output is JSON string
        assert tool_use_turn.content[0]["input"] == {"search_query": "Python code examples"}

        # Tool result should be JSON serialized
        parsed_output = json.loads(tool_result_turn.content[0]["content"])
        expected_output = {"results": ["Example 1: Hello World", "Example 2: Functions", "Example 3: Classes"]}
        assert parsed_output == expected_output

    @pytest.mark.asyncio
    async def test_empty_text_filtering(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_empty_text: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that empty text content is filtered out."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_empty_text],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Empty/whitespace-only text should be filtered out
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_multiple_text_blocks_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_message_with_multiple_text_blocks: MessageThreadDTO,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test processing message with multiple text blocks."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[anthropic_message_with_multiple_text_blocks],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Should create one conversation turn with multiple text content blocks
        assert len(result) == 1
        assert result[0].role == ConversationRole.ASSISTANT
        assert len(result[0].content) == 3

        assert result[0].content[0]["type"] == "text"
        assert result[0].content[0]["text"] == "First response part"

        assert result[0].content[1]["type"] == "text"
        assert result[0].content[1]["text"] == "Second response part"

        assert result[0].content[2]["type"] == "text"
        assert result[0].content[2]["text"] == "Third response part"

    @pytest.mark.asyncio
    async def test_empty_message_data_handling(
        self,
        anthropic_provider: Anthropic,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
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
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_empty",
            message_data=[],  # Empty message data
            prompt_type="user_query",
            prompt_category="general",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[empty_message],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_concurrent_attachment_processing(
        self,
        anthropic_provider: Anthropic,
        anthropic_mock_image_attachment_data: ChatAttachmentDataWithObjectBytes,
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
            return anthropic_mock_image_attachment_data

        async def get_image_data_2() -> ChatAttachmentDataWithObjectBytes:
            await asyncio.sleep(0.05)  # Different delay
            return anthropic_mock_image_attachment_data

        # Create messages with multiple attachments
        message1 = MessageThreadDTO(
            id=1,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[FileBlockData(content=FileContent(attachment_id=1))],
            prompt_type="user_query",
            prompt_category="file_upload",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        message2 = MessageThreadDTO(
            id=2,
            session_id=123,
            actor=MessageThreadActor.USER,
            query_id=1,
            message_type=MessageType.QUERY,
            conversation_chain=[1, 2],
            data_hash="hash_2",
            message_data=[FileBlockData(content=FileContent(attachment_id=2))],
            prompt_type="user_query",
            prompt_category="file_upload",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        attachment_task_map = {
            1: asyncio.create_task(get_image_data_1()),
            2: asyncio.create_task(get_image_data_2()),
        }

        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[message1, message2],
            attachment_data_task_map=attachment_task_map,
        )

        assert len(result) == 2
        # Both should be processed as image attachments
        assert all(turn.role == ConversationRole.USER for turn in result)
        assert all(len(turn.content) == 1 for turn in result)
        assert all(turn.content[0]["type"] == "image" for turn in result)

    @pytest.mark.asyncio
    async def test_return_type_consistency(
        self,
        anthropic_provider: Anthropic,
        anthropic_simple_conversation_history: List[MessageThreadDTO],
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
    ) -> None:
        """Test that return type is consistent with expected ConversationTurn structure."""
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=anthropic_simple_conversation_history,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert isinstance(result, list)
        for turn in result:
            assert isinstance(turn, ConversationTurn)
            assert hasattr(turn, "role")
            assert hasattr(turn, "content")
            assert isinstance(turn.role, ConversationRole)
            assert isinstance(turn.content, list)
            # Each content item should be a dict
            for content_item in turn.content:
                assert isinstance(content_item, dict)
                assert "type" in content_item

    @pytest.mark.asyncio
    async def test_large_conversation_processing_performance(
        self,
        anthropic_provider: Anthropic,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
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
                query_id=(i // 2) + 1,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                conversation_chain=list(range(1, i + 2)),
                data_hash=f"hash_{i}",
                message_data=[TextBlockData(content=TextBlockContent(text=f"Claude message {i + 1}"))],
                prompt_type="user_query" if i % 2 == 0 else "assistant_response",
                prompt_category="general",
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            large_conversation.append(message)

        start_time = time.time()
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=large_conversation,
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )
        end_time = time.time()

        assert len(result) == 100
        # Should process reasonably quickly (under 1 second for 100 messages)
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_tool_response_without_prior_request(
        self,
        anthropic_provider: Anthropic,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
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
            query_id=1,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[1],
            data_hash="hash_orphan",
            message_data=[
                ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="orphan_claude_tool",
                        tool_use_id="call_orphan_claude_999",
                        response="Orphaned Claude response",
                    )
                )
            ],
            prompt_type="tool_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[orphan_response],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        # Orphaned tool response should be ignored (no matching request)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_tool_request_storage_and_retrieval(
        self,
        anthropic_provider: Anthropic,
        anthropic_attachment_data_task_map_empty: Dict[int, asyncio.Task],
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
            query_id=1,
            message_type=MessageType.RESPONSE,
            conversation_chain=[1],
            data_hash="hash_1",
            message_data=[
                ToolUseRequestData(
                    content=ToolUseRequestContent(
                        tool_input={"test": "claude_data"},
                        tool_name="claude_test_tool",
                        tool_use_id="unique_claude_id_999",
                    )
                )
            ],
            prompt_type="assistant_response",
            prompt_category="tool_use",
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Process only the request - should store it but not output anything
        result = await anthropic_provider.get_conversation_turns(
            previous_responses=[tool_request],
            attachment_data_task_map=anthropic_attachment_data_task_map_empty,
        )

        assert len(result) == 0  # No output until response is matched
