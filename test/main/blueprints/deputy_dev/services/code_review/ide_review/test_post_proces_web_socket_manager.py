import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager import (
    PostProcessWebSocketManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    WebSocketMessage,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager_fixtures import (
    PostProcessWebSocketManagerFixtures,
)


class TestPostProcessWebSocketManager:
    """Test cases for PostProcessWebSocketManager class."""

    def test_init_with_default_local(self) -> None:
        """Test PostProcessWebSocketManager initialization with default local value."""
        # Arrange
        connection_id = "test_connection_123"
        
        # Act
        manager = PostProcessWebSocketManager(connection_id=connection_id)
        
        # Assert
        assert manager.connection_id == connection_id
        assert manager.is_local is False

    def test_init_with_local_true(self) -> None:
        """Test PostProcessWebSocketManager initialization with local=True."""
        # Arrange
        connection_id = "test_connection_456"
        is_local = True
        
        # Act
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=is_local)
        
        # Assert
        assert manager.connection_id == connection_id
        assert manager.is_local is True

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager.IdeReviewPostProcessor')
    async def test_process_request_success(self, mock_processor_class: Mock) -> None:
        """Test process_request executes successfully."""
        # Arrange
        connection_id = "test_connection_789"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_valid_request_data()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        expected_result = PostProcessWebSocketManagerFixtures.get_sample_post_process_result()
        
        mock_processor_instance = Mock()
        mock_processor_instance.post_process_pr = AsyncMock(return_value=expected_result)
        mock_processor_class.return_value = mock_processor_instance
        
        # Mock parent class methods
        @asynccontextmanager
        async def mock_progress_context(*args, **kwargs):
            yield
        
        manager.progress_context = mock_progress_context
        manager.push_to_connection_stream = AsyncMock()
        
        # Act
        await manager.process_request(request_data, local_testing_stream_buffer)
        
        # Assert
        mock_processor_instance.post_process_pr.assert_called_once_with(
            request_data, user_team_id=request_data["user_team_id"]
        )
        
        # Note: We can't easily verify the async context manager was called,
        # but the test would fail if it wasn't working properly
        
        # Verify messages were sent (3 messages: START, COMPLETE, STREAM_END)
        assert manager.push_to_connection_stream.call_count == 3

    @pytest.mark.asyncio
    async def test_process_request_missing_review_id(self) -> None:
        """Test process_request raises ValueError when review_id is missing."""
        # Arrange
        connection_id = "test_connection_error"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_request_data_without_review_id()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        # Mock parent class methods
        @asynccontextmanager
        async def mock_progress_context(*args, **kwargs):
            yield
        
        manager.progress_context = mock_progress_context
        manager.push_to_connection_stream = AsyncMock()
        
        # Act
        await manager.process_request(request_data, local_testing_stream_buffer)
        
        # Assert
        # Should have sent START, ERROR, and STREAM_END messages
        assert manager.push_to_connection_stream.call_count == 3
        
        # Check that error message was sent
        error_call = manager.push_to_connection_stream.call_args_list[1]
        error_message = error_call[0][0]
        assert error_message.type == "POST_PROCESS_ERROR"
        assert "review_id is required" in error_message.data["message"]

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager.IdeReviewPostProcessor')
    async def test_process_request_processor_exception(self, mock_processor_class: Mock) -> None:
        """Test process_request handles processor exceptions."""
        # Arrange
        connection_id = "test_connection_exception"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_valid_request_data()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        mock_processor_instance = Mock()
        mock_processor_instance.post_process_pr = AsyncMock(side_effect=Exception("Processor error"))
        mock_processor_class.return_value = mock_processor_instance
        
        # Mock parent class methods
        @asynccontextmanager
        async def mock_progress_context(*args, **kwargs):
            yield
        
        manager.progress_context = mock_progress_context
        manager.push_to_connection_stream = AsyncMock()
        
        # Act
        await manager.process_request(request_data, local_testing_stream_buffer)
        
        # Assert
        # Should have sent START, ERROR, and STREAM_END messages
        assert manager.push_to_connection_stream.call_count == 3
        
        # Check that error message was sent
        error_call = manager.push_to_connection_stream.call_args_list[1]
        error_message = error_call[0][0]
        assert error_message.type == "POST_PROCESS_ERROR"
        assert "Processor error" in error_message.data["message"]

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager.IdeReviewPostProcessor')
    async def test_process_request_message_sequence(self, mock_processor_class: Mock) -> None:
        """Test process_request sends messages in correct sequence."""
        # Arrange
        connection_id = "test_connection_sequence"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_valid_request_data()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        expected_result = PostProcessWebSocketManagerFixtures.get_sample_post_process_result()
        
        mock_processor_instance = Mock()
        mock_processor_instance.post_process_pr = AsyncMock(return_value=expected_result)
        mock_processor_class.return_value = mock_processor_instance
        
        # Mock parent class methods
        @asynccontextmanager
        async def mock_progress_context(*args, **kwargs):
            yield
        
        manager.progress_context = mock_progress_context
        manager.push_to_connection_stream = AsyncMock()
        
        # Act
        await manager.process_request(request_data, local_testing_stream_buffer)
        
        # Assert
        calls = manager.push_to_connection_stream.call_args_list
        assert len(calls) == 3
        
        # Check message sequence
        assert calls[0][0][0].type == "POST_PROCESS_START"
        assert calls[1][0][0].type == "POST_PROCESS_COMPLETE"
        assert calls[2][0][0].type == "STREAM_END"
        
        # Check complete message content
        complete_message = calls[1][0][0]
        assert complete_message.data["result"] == expected_result
        assert complete_message.data["progress"] == 100

    @pytest.mark.asyncio
    @patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager.IdeReviewPostProcessor')
    async def test_process_request_with_none_result(self, mock_processor_class: Mock) -> None:
        """Test process_request handles None result from processor."""
        # Arrange
        connection_id = "test_connection_none"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_valid_request_data()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        mock_processor_instance = Mock()
        mock_processor_instance.post_process_pr = AsyncMock(return_value=None)
        mock_processor_class.return_value = mock_processor_instance
        
        # Mock parent class methods
        @asynccontextmanager
        async def mock_progress_context(*args, **kwargs):
            yield
        
        manager.progress_context = mock_progress_context
        manager.push_to_connection_stream = AsyncMock()
        
        # Act
        await manager.process_request(request_data, local_testing_stream_buffer)
        
        # Assert
        complete_call = manager.push_to_connection_stream.call_args_list[1]
        complete_message = complete_call[0][0]
        assert complete_message.data["result"] == {"status": "SUCCESS"}

    @pytest.mark.asyncio
    async def test_process_post_process_task_success(self) -> None:
        """Test process_post_process_task executes successfully."""
        # Arrange
        connection_id = "test_connection_task"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_valid_request_data()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        # Mock methods
        manager.process_request = AsyncMock()
        manager.cleanup = AsyncMock()
        
        # Act
        await manager.process_post_process_task(request_data, local_testing_stream_buffer)
        
        # Assert
        manager.process_request.assert_called_once_with(request_data, local_testing_stream_buffer)
        manager.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_post_process_task_exception(self) -> None:
        """Test process_post_process_task handles exceptions."""
        # Arrange
        connection_id = "test_connection_task_error"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_valid_request_data()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        # Mock methods
        manager.process_request = AsyncMock(side_effect=Exception("Task error"))
        manager.send_error_message = AsyncMock()
        manager.cleanup = AsyncMock()
        
        # Act
        await manager.process_post_process_task(request_data, local_testing_stream_buffer)
        
        # Assert
        manager.send_error_message.assert_called_once_with(
            "Background task error: Task error", local_testing_stream_buffer
        )
        manager.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_request_user_team_id_handling(self) -> None:
        """Test process_request correctly handles user_team_id parameter."""
        # Arrange
        connection_id = "test_connection_team"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_request_data_with_user_team_id()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager.IdeReviewPostProcessor') as mock_processor_class:
            mock_processor_instance = Mock()
            mock_processor_instance.post_process_pr = AsyncMock(return_value={})
            mock_processor_class.return_value = mock_processor_instance
            
            # Mock parent class methods
            @asynccontextmanager
            async def mock_progress_context(*args, **kwargs):
                yield
            
            manager.progress_context = mock_progress_context
            manager.push_to_connection_stream = AsyncMock()
            
            # Act
            await manager.process_request(request_data, local_testing_stream_buffer)
            
            # Assert
            mock_processor_instance.post_process_pr.assert_called_once_with(
                request_data, user_team_id=request_data["user_team_id"]
            )

    @pytest.mark.asyncio
    async def test_process_request_without_user_team_id(self) -> None:
        """Test process_request handles missing user_team_id."""
        # Arrange
        connection_id = "test_connection_no_team"
        manager = PostProcessWebSocketManager(connection_id=connection_id, is_local=True)
        
        request_data = PostProcessWebSocketManagerFixtures.get_request_data_without_user_team_id()
        local_testing_stream_buffer = PostProcessWebSocketManagerFixtures.get_empty_stream_buffer()
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager.IdeReviewPostProcessor') as mock_processor_class:
            mock_processor_instance = Mock()
            mock_processor_instance.post_process_pr = AsyncMock(return_value={})
            mock_processor_class.return_value = mock_processor_instance
            
            # Mock parent class methods
            @asynccontextmanager
            async def mock_progress_context(*args, **kwargs):
                yield
            
            manager.progress_context = mock_progress_context
            manager.push_to_connection_stream = AsyncMock()
            
            # Act
            await manager.process_request(request_data, local_testing_stream_buffer)
            
            # Assert
            mock_processor_instance.post_process_pr.assert_called_once_with(
                request_data, user_team_id=None
            )