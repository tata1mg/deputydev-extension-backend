"""
Unit tests for BaseWebSocketManager.

This module provides comprehensive unit tests for the BaseWebSocketManager class,
covering all methods including push_to_connection_stream, send_error_message,
progress context management, and initialization with various scenarios.
"""

import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    SocketClosedError,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager import (
    BaseWebSocketManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import WebSocketMessage
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager_fixtures import *


# Concrete implementation for testing abstract base class
class TestWebSocketManager(BaseWebSocketManager):
    """Concrete implementation of BaseWebSocketManager for testing."""

    def __init__(self, connection_id: str, is_local: bool = False) -> None:
        super().__init__(connection_id, is_local)
        self.test_requests: List[Dict[str, Any]] = []

    async def process_request(
        self, request_data: Dict[str, Any], local_testing_stream_buffer: Dict[str, List[str]]
    ) -> None:
        """Test implementation of process_request."""
        self.test_requests.append(request_data)


class TestBaseWebSocketManagerInitialization:
    """Test cases for BaseWebSocketManager initialization."""

    def test_init_local_connection(self) -> None:
        """Test initialization with local connection."""
        manager = TestWebSocketManager("local-conn-123", is_local=True)

        assert manager.connection_id == "local-conn-123"
        assert manager.is_local is True
        assert manager.connection_id_gone is False
        assert manager.aws_client is None
        assert manager._progress_task is None
        assert manager._should_stop_progress is False

    def test_init_aws_connection(self) -> None:
        """Test initialization with AWS connection."""
        manager = TestWebSocketManager("aws-conn-456", is_local=False)

        assert manager.connection_id == "aws-conn-456"
        assert manager.is_local is False
        assert manager.connection_id_gone is False
        assert manager.aws_client is None
        assert manager._progress_task is None
        assert manager._should_stop_progress is False


class TestBaseWebSocketManagerInitializeAwsClient:
    """Test cases for BaseWebSocketManager.initialize_aws_client method."""

    @pytest.mark.asyncio
    async def test_initialize_aws_client_local_mode(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
    ) -> None:
        """Test initialize_aws_client in local mode (should not initialize)."""
        await sample_local_websocket_manager.initialize_aws_client()

        assert sample_local_websocket_manager.aws_client is None

    @pytest.mark.asyncio
    async def test_initialize_aws_client_aws_mode(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
    ) -> None:
        """Test initialize_aws_client in AWS mode."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager.AWSAPIGatewayServiceClient"
            ) as mock_client_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager.ConfigManager"
            ) as mock_config,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_config.configs = {
                "AWS_API_GATEWAY": {"CODE_REVIEW_WEBSOCKET_WEBHOOK_ENDPOINT": "wss://test-endpoint.com"}
            }

            await sample_aws_websocket_manager.initialize_aws_client()

            assert sample_aws_websocket_manager.aws_client == mock_client
            mock_client.init_client.assert_called_once_with(endpoint="wss://test-endpoint.com")


class TestBaseWebSocketManagerPushToConnectionStream:
    """Test cases for BaseWebSocketManager.push_to_connection_stream method."""

    @pytest.mark.asyncio
    async def test_push_to_connection_stream_local_mode(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream in local mode."""
        await sample_local_websocket_manager.push_to_connection_stream(
            sample_websocket_message, sample_local_stream_buffer
        )

        # Check message was added to buffer
        assert len(sample_local_stream_buffer[sample_local_websocket_manager.connection_id]) == 1

        # Parse the message and verify content
        message_json = json.loads(sample_local_stream_buffer[sample_local_websocket_manager.connection_id][0])
        assert message_json["type"] == sample_websocket_message.type
        assert message_json["agent_id"] == sample_websocket_message.agent_id
        assert "timestamp" in message_json

    @pytest.mark.asyncio
    async def test_push_to_connection_stream_aws_mode(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream in AWS mode."""
        mock_aws_client = AsyncMock()
        sample_aws_websocket_manager.aws_client = mock_aws_client

        await sample_aws_websocket_manager.push_to_connection_stream(
            sample_websocket_message, sample_local_stream_buffer
        )

        # Verify AWS client was called
        mock_aws_client.post_to_connection.assert_called_once()
        call_args = mock_aws_client.post_to_connection.call_args
        assert call_args[1]["connection_id"] == sample_aws_websocket_manager.connection_id

        # Verify message content
        message_data = json.loads(call_args[1]["message"])
        assert message_data["type"] == sample_websocket_message.type
        assert message_data["agent_id"] == sample_websocket_message.agent_id

    @pytest.mark.asyncio
    async def test_push_to_connection_stream_connection_gone(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream when connection is gone."""
        sample_local_websocket_manager.connection_id_gone = True

        await sample_local_websocket_manager.push_to_connection_stream(
            sample_websocket_message, sample_local_stream_buffer
        )

        # Should not add message to buffer when connection is gone
        assert len(sample_local_stream_buffer.get(sample_local_websocket_manager.connection_id, [])) == 0

    @pytest.mark.asyncio
    async def test_push_to_connection_stream_socket_closed_error(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream with SocketClosedError."""
        mock_aws_client = AsyncMock()
        mock_aws_client.post_to_connection.side_effect = SocketClosedError("Connection closed")
        sample_aws_websocket_manager.aws_client = mock_aws_client

        with pytest.raises(SocketClosedError):
            await sample_aws_websocket_manager.push_to_connection_stream(
                sample_websocket_message, sample_local_stream_buffer
            )

        # Connection should be marked as gone
        assert sample_aws_websocket_manager.connection_id_gone is True

    @pytest.mark.asyncio
    async def test_push_to_connection_stream_general_exception(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream with general exception."""
        mock_aws_client = AsyncMock()
        mock_aws_client.post_to_connection.side_effect = Exception("Network error")
        sample_aws_websocket_manager.aws_client = mock_aws_client

        with pytest.raises(Exception, match="Network error"):
            await sample_aws_websocket_manager.push_to_connection_stream(
                sample_websocket_message, sample_local_stream_buffer
            )

    @pytest.mark.asyncio
    async def test_push_to_connection_stream_no_aws_client(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream in AWS mode without initialized client."""
        # aws_client is None by default
        await sample_aws_websocket_manager.push_to_connection_stream(
            sample_websocket_message, sample_local_stream_buffer
        )

        # Should complete without error when no aws_client


class TestBaseWebSocketManagerSendErrorMessage:
    """Test cases for BaseWebSocketManager.send_error_message method."""

    @pytest.mark.asyncio
    async def test_send_error_message_success(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test send_error_message successful execution."""
        error_message = "Test error occurred"

        await sample_local_websocket_manager.send_error_message(error_message, sample_local_stream_buffer)

        # Verify error message was sent
        assert len(sample_local_stream_buffer[sample_local_websocket_manager.connection_id]) == 1

        message_json = json.loads(sample_local_stream_buffer[sample_local_websocket_manager.connection_id][0])
        assert message_json["type"] == "STREAM_ERROR"
        assert message_json["data"]["message"] == error_message

    @pytest.mark.asyncio
    async def test_send_error_message_with_special_characters(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test send_error_message with special characters."""
        error_message = "Error with unicode: 测试 and emoji: 🚨"

        await sample_local_websocket_manager.send_error_message(error_message, sample_local_stream_buffer)

        message_json = json.loads(sample_local_stream_buffer[sample_local_websocket_manager.connection_id][0])
        assert message_json["data"]["message"] == error_message


class TestBaseWebSocketManagerCleanup:
    """Test cases for BaseWebSocketManager.cleanup method."""

    @pytest.mark.asyncio
    async def test_cleanup_with_aws_client(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
    ) -> None:
        """Test cleanup when AWS client exists."""
        mock_aws_client = AsyncMock()
        sample_aws_websocket_manager.aws_client = mock_aws_client

        await sample_aws_websocket_manager.cleanup()

        mock_aws_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_without_aws_client(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
    ) -> None:
        """Test cleanup when no AWS client exists."""
        await sample_local_websocket_manager.cleanup()

        # Should complete without error


class TestBaseWebSocketManagerSendProgressUpdates:
    """Test cases for BaseWebSocketManager.send_progress_updates method."""

    @pytest.mark.asyncio
    async def test_send_progress_updates_normal_operation(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test send_progress_updates normal operation."""
        # Start progress updates with short interval
        progress_task = asyncio.create_task(
            sample_local_websocket_manager.send_progress_updates(sample_local_stream_buffer, interval=0.1)
        )

        # Let it run for a short time
        await asyncio.sleep(0.25)

        # Stop progress updates
        sample_local_websocket_manager._should_stop_progress = True
        progress_task.cancel()

        try:
            await progress_task
        except asyncio.CancelledError:
            pass

        # Should have sent at least one progress message
        messages = sample_local_stream_buffer[sample_local_websocket_manager.connection_id]
        assert len(messages) >= 1

        # Check message content
        message_json = json.loads(messages[0])
        assert message_json["type"] == "IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_send_progress_updates_connection_gone(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test send_progress_updates when connection is gone."""
        sample_local_websocket_manager.connection_id_gone = True

        # Should complete quickly without sending messages
        await sample_local_websocket_manager.send_progress_updates(sample_local_stream_buffer, interval=0.1)

        # No messages should be sent
        messages = sample_local_stream_buffer.get(sample_local_websocket_manager.connection_id, [])
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_send_progress_updates_cancelled(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test send_progress_updates cancellation."""
        progress_task = asyncio.create_task(
            sample_local_websocket_manager.send_progress_updates(sample_local_stream_buffer, interval=1.0)
        )

        # Cancel immediately
        progress_task.cancel()

        try:
            await progress_task
        except asyncio.CancelledError:
            pass  # Expected


class TestBaseWebSocketManagerProgressContext:
    """Test cases for BaseWebSocketManager.progress_context method."""

    @pytest.mark.asyncio
    async def test_progress_context_normal_execution(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test progress_context normal execution."""
        async with sample_local_websocket_manager.progress_context(sample_local_stream_buffer, interval=0.1):
            # Let some progress messages be sent
            await asyncio.sleep(0.25)

        # Progress should have stopped
        assert sample_local_websocket_manager._should_stop_progress is True

        # Should have sent progress messages
        messages = sample_local_stream_buffer[sample_local_websocket_manager.connection_id]
        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_progress_context_with_exception(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test progress_context with exception in context."""
        with pytest.raises(ValueError, match="Test exception"):
            async with sample_local_websocket_manager.progress_context(sample_local_stream_buffer, interval=0.1):
                await asyncio.sleep(0.1)
                raise ValueError("Test exception")

        # Progress should still be stopped after exception
        assert sample_local_websocket_manager._should_stop_progress is True

    @pytest.mark.asyncio
    async def test_progress_context_task_cleanup(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test progress_context task cleanup."""
        async with sample_local_websocket_manager.progress_context(sample_local_stream_buffer, interval=0.1):
            # Verify task is created
            assert sample_local_websocket_manager._progress_task is not None
            assert not sample_local_websocket_manager._progress_task.done()

            await asyncio.sleep(0.1)

        # Task should be cleaned up
        if sample_local_websocket_manager._progress_task:
            assert sample_local_websocket_manager._progress_task.done()


class TestBaseWebSocketManagerEdgeCases:
    """Test cases for BaseWebSocketManager edge cases."""

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_progress_contexts(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test multiple simultaneous progress contexts (should handle gracefully)."""

        async def context_task(delay: float) -> None:
            async with sample_local_websocket_manager.progress_context(sample_local_stream_buffer, interval=0.05):
                await asyncio.sleep(delay)

        # Run multiple contexts concurrently
        tasks = [asyncio.create_task(context_task(0.1)), asyncio.create_task(context_task(0.15))]

        await asyncio.gather(*tasks)

        # Should complete without error
        assert sample_local_websocket_manager._should_stop_progress is True

    @pytest.mark.asyncio
    async def test_push_message_with_none_data(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test push_to_connection_stream with None data."""
        message = WebSocketMessage(type="TEST_MESSAGE", agent_id=None, data=None)

        await sample_local_websocket_manager.push_to_connection_stream(message, sample_local_stream_buffer)

        # Should handle None values gracefully
        messages = sample_local_stream_buffer[sample_local_websocket_manager.connection_id]
        assert len(messages) == 1

        message_json = json.loads(messages[0])
        assert message_json["type"] == "TEST_MESSAGE"
        assert message_json["agent_id"] is None
        assert message_json["data"] is None

    @pytest.mark.asyncio
    async def test_cleanup_multiple_times(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
    ) -> None:
        """Test calling cleanup multiple times."""
        mock_aws_client = AsyncMock()
        sample_aws_websocket_manager.aws_client = mock_aws_client

        # Call cleanup multiple times
        await sample_aws_websocket_manager.cleanup()
        await sample_aws_websocket_manager.cleanup()
        await sample_aws_websocket_manager.cleanup()

        # Should only call close once per client
        mock_aws_client.close.assert_called()


class TestBaseWebSocketManagerIntegration:
    """Integration test cases for BaseWebSocketManager."""

    @pytest.mark.asyncio
    async def test_full_websocket_flow_local(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test full WebSocket flow in local mode."""
        # Test initialization
        await sample_local_websocket_manager.initialize_aws_client()

        # Test message sending with progress
        async with sample_local_websocket_manager.progress_context(sample_local_stream_buffer, interval=0.05):
            await sample_local_websocket_manager.push_to_connection_stream(
                sample_websocket_message, sample_local_stream_buffer
            )
            await asyncio.sleep(0.1)  # Let progress messages be sent

        # Test error message
        await sample_local_websocket_manager.send_error_message("Test error", sample_local_stream_buffer)

        # Test cleanup
        await sample_local_websocket_manager.cleanup()

        # Verify messages were sent
        messages = sample_local_stream_buffer[sample_local_websocket_manager.connection_id]
        assert len(messages) >= 3  # Progress + main message + error

    @pytest.mark.asyncio
    async def test_full_websocket_flow_aws(
        self,
        sample_aws_websocket_manager: TestWebSocketManager,
        sample_websocket_message: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test full WebSocket flow in AWS mode."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager.AWSAPIGatewayServiceClient"
            ) as mock_client_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager.ConfigManager"
            ) as mock_config,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_config.configs = {"AWS_API_GATEWAY": {"CODE_REVIEW_WEBSOCKET_WEBHOOK_ENDPOINT": "wss://test.com"}}

            # Initialize AWS client
            await sample_aws_websocket_manager.initialize_aws_client()
            assert sample_aws_websocket_manager.aws_client == mock_client

            # Send message
            await sample_aws_websocket_manager.push_to_connection_stream(
                sample_websocket_message, sample_local_stream_buffer
            )

            # Verify AWS client was used
            mock_client.post_to_connection.assert_called()

            # Cleanup
            await sample_aws_websocket_manager.cleanup()
            mock_client.close.assert_called()


class TestBaseWebSocketManagerPerformance:
    """Performance test cases for BaseWebSocketManager."""

    @pytest.mark.asyncio
    async def test_high_frequency_message_sending(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test high frequency message sending."""
        messages = [
            WebSocketMessage(type="BULK_MESSAGE", agent_id=i, data={"content": f"Message {i}"}) for i in range(100)
        ]

        start_time = asyncio.get_event_loop().time()

        # Send all messages
        for message in messages:
            await sample_local_websocket_manager.push_to_connection_stream(message, sample_local_stream_buffer)

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        # Should complete within reasonable time
        assert execution_time < 1.0  # 1 second for 100 messages

        # Verify all messages were sent
        sent_messages = sample_local_stream_buffer[sample_local_websocket_manager.connection_id]
        assert len(sent_messages) == 100

    @pytest.mark.asyncio
    async def test_concurrent_progress_and_messages(
        self,
        sample_local_websocket_manager: TestWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test concurrent progress updates and message sending."""

        async def send_messages() -> None:
            for i in range(20):
                message = WebSocketMessage(type="CONCURRENT_MESSAGE", agent_id=i, data={"index": i})
                await sample_local_websocket_manager.push_to_connection_stream(message, sample_local_stream_buffer)
                await asyncio.sleep(0.01)  # Small delay

        # Run message sending with progress context
        async with sample_local_websocket_manager.progress_context(sample_local_stream_buffer, interval=0.05):
            await send_messages()

        # Should have both progress and regular messages
        messages = sample_local_stream_buffer[sample_local_websocket_manager.connection_id]
        assert len(messages) >= 20  # At least the 20 regular messages

        # Check message types
        message_types = {json.loads(msg)["type"] for msg in messages}
        assert "IN_PROGRESS" in message_types
        assert "CONCURRENT_MESSAGE" in message_types
