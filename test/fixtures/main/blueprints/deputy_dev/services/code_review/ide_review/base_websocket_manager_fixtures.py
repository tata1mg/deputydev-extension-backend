"""
Fixtures for BaseWebSocketManager tests.

This module provides fixtures for testing the BaseWebSocketManager class,
including sample data, mocked objects, and test configurations.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager import (
    BaseWebSocketManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import WebSocketMessage


# Test implementation of abstract BaseWebSocketManager
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


@pytest.fixture
def sample_local_websocket_manager() -> TestWebSocketManager:
    """Create a sample WebSocketManager for local testing."""
    return TestWebSocketManager("local-test-conn-123", is_local=True)


@pytest.fixture
def sample_aws_websocket_manager() -> TestWebSocketManager:
    """Create a sample WebSocketManager for AWS testing."""
    return TestWebSocketManager("aws-test-conn-456", is_local=False)


@pytest.fixture
def sample_websocket_message() -> WebSocketMessage:
    """Create a sample WebSocket message."""
    return WebSocketMessage(
        type="TEST_MESSAGE",
        agent_id=12345,
        data={
            "content": "This is a test message",
            "status": "success",
            "details": {"processed_at": "2024-01-15T10:30:00Z", "version": "1.0"},
        },
    )


@pytest.fixture
def sample_websocket_message_with_none_data() -> WebSocketMessage:
    """Create a sample WebSocket message with None data."""
    return WebSocketMessage(type="NULL_DATA_MESSAGE", agent_id=None, data=None)


@pytest.fixture
def sample_websocket_message_error() -> WebSocketMessage:
    """Create a sample WebSocket error message."""
    return WebSocketMessage(
        type="ERROR_MESSAGE",
        agent_id=67890,
        data={"error": "Something went wrong", "error_code": "ERR_001", "stack_trace": "Error occurred at line 42"},
    )


@pytest.fixture
def sample_websocket_message_tool_use() -> WebSocketMessage:
    """Create a sample WebSocket message for tool use."""
    return WebSocketMessage(
        type="TOOL_USE_REQUEST",
        agent_id=11111,
        data={
            "tool_name": "file_reader",
            "tool_input": {"file_path": "src/main.py", "start_line": 1, "end_line": 50},
            "tool_use_id": "tool-use-123",
        },
    )


@pytest.fixture
def sample_local_stream_buffer() -> Dict[str, List[str]]:
    """Create a sample local stream buffer."""
    return {"local-test-conn-123": [], "aws-test-conn-456": []}


@pytest.fixture
def sample_connection_id() -> str:
    """Create a sample connection ID."""
    return "websocket-connection-abc123"


@pytest.fixture
def sample_aws_endpoint() -> str:
    """Create a sample AWS WebSocket endpoint."""
    return "wss://api.example.com/dev/websocket"


@pytest.fixture
def sample_error_message() -> str:
    """Create a sample error message."""
    return "A critical error occurred during processing"


@pytest.fixture
def sample_error_message_with_unicode() -> str:
    """Create a sample error message with unicode characters."""
    return "Error occurred: 测试错误 🚨 Special chars: áéíóú"


@pytest.fixture
def sample_progress_interval() -> float:
    """Create a sample progress update interval."""
    return 0.5  # 500ms


@pytest.fixture
def sample_progress_short_interval() -> float:
    """Create a short progress update interval for testing."""
    return 0.01  # 10ms


@pytest.fixture
def sample_aws_config() -> Dict[str, Any]:
    """Create sample AWS configuration."""
    return {"AWS_API_GATEWAY": {"CODE_REVIEW_WEBSOCKET_WEBHOOK_ENDPOINT": "wss://test-api.amazonaws.com/dev/websocket"}}


@pytest.fixture
def sample_websocket_messages_bulk() -> List[WebSocketMessage]:
    """Create multiple WebSocket messages for bulk testing."""
    return [
        WebSocketMessage(
            type="BULK_MESSAGE",
            agent_id=i,
            data={"message_id": i, "content": f"Bulk message {i}", "batch": "test_batch_001"},
        )
        for i in range(1, 21)  # 20 messages
    ]


@pytest.fixture
def sample_concurrent_messages() -> List[WebSocketMessage]:
    """Create WebSocket messages for concurrent testing."""
    return [
        WebSocketMessage(
            type="CONCURRENT_MESSAGE",
            agent_id=1000 + i,
            data={"thread_id": i, "concurrent_test": True, "timestamp": f"2024-01-15T10:30:{str(i).zfill(2)}Z"},
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_large_message_data() -> Dict[str, Any]:
    """Create large message data for performance testing."""
    return {
        "large_content": "x" * 10000,  # 10KB of data
        "repeated_data": ["item"] * 1000,
        "nested_structure": {"level1": {"level2": {"level3": {"data": list(range(1000))}}}},
    }


@pytest.fixture
def sample_websocket_message_large(sample_large_message_data: Dict[str, Any]) -> WebSocketMessage:
    """Create a WebSocket message with large data payload."""
    return WebSocketMessage(type="LARGE_MESSAGE", agent_id=99999, data=sample_large_message_data)


@pytest.fixture
def sample_special_characters_data() -> Dict[str, Any]:
    """Create data with special characters and unicode."""
    return {
        "unicode_text": "Testing unicode: 你好世界 🌍 Héllö Wörld",
        "special_chars": "!@#$%^&*()_+-=[]{}|;:'\",.<>?/~`",
        "escape_sequences": "Line1\nLine2\tTabbed\r\nWindows",
        "json_breaking": '{"nested": "value with \\"quotes\\""}',
        "emojis": "🚀🔥💡⚡🎉🎯📊🔍",
    }


@pytest.fixture
def sample_websocket_message_special_chars(sample_special_characters_data: Dict[str, Any]) -> WebSocketMessage:
    """Create a WebSocket message with special characters."""
    return WebSocketMessage(type="SPECIAL_CHARS_MESSAGE", agent_id=55555, data=sample_special_characters_data)


@pytest.fixture
def sample_mock_aws_client() -> MagicMock:
    """Create a mock AWS API Gateway client."""
    mock_client = MagicMock()
    mock_client.init_client = MagicMock()
    mock_client.post_to_connection = MagicMock()
    mock_client.close = MagicMock()
    return mock_client


@pytest.fixture
def sample_websocket_managers_multiple() -> List[TestWebSocketManager]:
    """Create multiple WebSocket managers for concurrent testing."""
    return [TestWebSocketManager(f"conn-{i}", is_local=(i % 2 == 0)) for i in range(5)]


@pytest.fixture
def sample_progress_test_data() -> Dict[str, Any]:
    """Create test data for progress functionality."""
    return {
        "short_interval": 0.01,  # 10ms
        "medium_interval": 0.05,  # 50ms
        "long_interval": 0.1,  # 100ms
        "test_duration": 0.2,  # 200ms total test time
        "expected_min_messages": 1,
        "expected_max_messages": 25,
    }


@pytest.fixture
def sample_error_scenarios() -> List[Dict[str, Any]]:
    """Create various error scenarios for testing."""
    return [
        {
            "error_type": "socket_closed",
            "exception_class": "SocketClosedError",
            "message": "WebSocket connection closed by client",
            "should_mark_gone": True,
        },
        {
            "error_type": "network_error",
            "exception_class": "Exception",
            "message": "Network timeout occurred",
            "should_mark_gone": False,
        },
        {
            "error_type": "permission_error",
            "exception_class": "PermissionError",
            "message": "Access denied to WebSocket endpoint",
            "should_mark_gone": False,
        },
        {
            "error_type": "json_error",
            "exception_class": "ValueError",
            "message": "Invalid JSON format in message",
            "should_mark_gone": False,
        },
    ]


@pytest.fixture
def sample_cleanup_scenarios() -> List[Dict[str, Any]]:
    """Create cleanup test scenarios."""
    return [
        {"has_aws_client": True, "client_raises_error": False, "expected_calls": 1},
        {"has_aws_client": True, "client_raises_error": True, "expected_calls": 1},
        {"has_aws_client": False, "client_raises_error": False, "expected_calls": 0},
    ]


@pytest.fixture
def sample_message_timestamps() -> List[str]:
    """Create sample timestamps for message testing."""
    return [
        "2024-01-15T10:00:00.000Z",
        "2024-01-15T10:00:01.123Z",
        "2024-01-15T10:00:02.456Z",
        "2024-01-15T10:00:03.789Z",
        "2024-01-15T10:00:04.999Z",
    ]


@pytest.fixture
def sample_context_manager_test_data() -> Dict[str, Any]:
    """Create test data for context manager functionality."""
    return {
        "intervals": [0.01, 0.02, 0.05],
        "execution_times": [0.1, 0.2, 0.3],
        "exception_scenarios": [
            None,  # No exception
            ValueError("Test exception"),
            RuntimeError("Runtime error"),
            KeyboardInterrupt(),
        ],
    }


@pytest.fixture
def sample_performance_test_config() -> Dict[str, Any]:
    """Create configuration for performance testing."""
    return {
        "message_counts": [10, 50, 100, 500],
        "interval_ranges": [0.001, 0.01, 0.1],
        "max_execution_time": 5.0,  # seconds
        "memory_threshold": 100 * 1024 * 1024,  # 100MB
        "concurrent_connections": [1, 5, 10],
    }


@pytest.fixture
def sample_integration_test_flow() -> List[Dict[str, Any]]:
    """Create integration test flow steps."""
    return [
        {"step": "initialize", "action": "initialize_aws_client", "expected_result": "client_set"},
        {"step": "start_progress", "action": "start_progress_context", "expected_result": "progress_started"},
        {"step": "send_messages", "action": "send_multiple_messages", "expected_result": "messages_sent"},
        {"step": "send_error", "action": "send_error_message", "expected_result": "error_sent"},
        {"step": "stop_progress", "action": "stop_progress_context", "expected_result": "progress_stopped"},
        {"step": "cleanup", "action": "cleanup_resources", "expected_result": "resources_cleaned"},
    ]
