import asyncio
import json
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncContextManager, Dict, List, Optional

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    AWSAPIGatewayServiceClient,
    SocketClosedException,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import WebSocketMessage


class BaseWebSocketManager(ABC):
    """
    Base class for managing websocket communication for extension review.
    Provides common functionality for AWS websocket connections and local testing.
    """

    def __init__(self, connection_id: str, is_local: bool = False) -> None:
        self.connection_id = connection_id
        self.is_local = is_local
        self.connection_id_gone = False
        self.aws_client: Optional[AWSAPIGatewayServiceClient] = None
        self._progress_task: Optional[asyncio.Task] = None
        self._should_stop_progress = False

    async def initialize_aws_client(self) -> None:
        """Initialize AWS WebSocket client."""
        if not self.is_local:
            self.aws_client = AWSAPIGatewayServiceClient()
            await self.aws_client.init_client(
                endpoint=f"{ConfigManager.configs['AWS_API_GATEWAY']['CODE_REVIEW_WEBSOCKET_WEBHOOK_ENDPOINT']}"
            )

    async def push_to_connection_stream(
        self, message: WebSocketMessage, local_testing_stream_buffer: Dict[str, List[str]]
    ) -> None:
        """
        Push message to WebSocket connection.

        Args:
            message: WebSocket message to send
            local_testing_stream_buffer: Buffer for local testing
        """
        if self.connection_id_gone:
            return

        # Add timestamp to message
        message.timestamp = datetime.utcnow().isoformat()
        message_data = message.model_dump(mode="json")

        try:
            if self.is_local:
                # Local testing - use buffer
                local_testing_stream_buffer.setdefault(self.connection_id, []).append(json.dumps(message_data))
            else:
                # AWS WebSocket
                if self.aws_client:
                    await self.aws_client.post_to_connection(
                        connection_id=self.connection_id,
                        message=json.dumps(message_data),
                    )
        except SocketClosedException:
            self.connection_id_gone = True
            AppLogger.log_error(f"WebSocket connection {self.connection_id} closed")
            raise
        except Exception as e:  # noqa: BLE001
            AppLogger.log_error(f"Error pushing to WebSocket {self.connection_id}: {e}")
            raise

    async def send_error_message(self, error_message: str, local_testing_stream_buffer: Dict[str, List[str]]) -> None:
        """Send error message to websocket connection."""
        await self.push_to_connection_stream(
            WebSocketMessage(type="STREAM_ERROR", data={"message": error_message}), local_testing_stream_buffer
        )

    async def cleanup(self) -> None:
        """Clean up AWS client and other resources."""
        if self.aws_client:
            await self.aws_client.close()

    @abstractmethod
    async def process_request(
        self, request_data: Dict[str, Any], local_testing_stream_buffer: Dict[str, List[str]]
    ) -> None:
        """
        Abstract method to process the specific request.
        Must be implemented by subclasses.
        """
        pass

    async def send_progress_updates(
        self, local_testing_stream_buffer: Dict[str, List[str]], interval: int = 10
    ) -> None:
        """
        Send periodic IN_PROGRESS messages while a task is running.

        Args:
            local_testing_stream_buffer: Buffer for local testing
            interval: Interval in seconds between progress updates
        """
        try:
            while not self._should_stop_progress:
                if self.connection_id_gone:
                    break

                await self.push_to_connection_stream(
                    WebSocketMessage(
                        type="IN_PROGRESS",
                    ),
                    local_testing_stream_buffer,
                )

                try:
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break

        except asyncio.CancelledError:
            AppLogger.log_info(f"Progress updates cancelled for connection {self.connection_id}")
        except Exception as e:  # noqa: BLE001
            AppLogger.log_error(f"Error sending progress updates for connection {self.connection_id}: {e}")

    @asynccontextmanager
    async def progress_context(
        self, local_testing_stream_buffer: Dict[str, List[str]], interval: int = 10
    ) -> AsyncContextManager[None]:
        """
        Context manager for handling progress updates during request processing.

        Args:
            local_testing_stream_buffer: Buffer for local testing
            interval: Interval in seconds between progress updates
        """
        self._should_stop_progress = False
        self._progress_task = asyncio.create_task(self.send_progress_updates(local_testing_stream_buffer, interval))

        try:
            yield
        finally:
            self._should_stop_progress = True
            if self._progress_task and not self._progress_task.done():
                self._progress_task.cancel()
                try:
                    await self._progress_task
                except asyncio.CancelledError:
                    pass
