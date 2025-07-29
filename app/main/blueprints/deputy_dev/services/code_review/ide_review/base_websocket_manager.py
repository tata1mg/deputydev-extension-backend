import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    AWSAPIGatewayServiceClient,
    SocketClosedException,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    WebSocketMessage,
)
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager


class BaseWebSocketManager(ABC):
    """
    Base class for managing websocket communication for extension review.
    Provides common functionality for AWS websocket connections and local testing.
    """

    def __init__(self, connection_id: str, is_local: bool = False):
        self.connection_id = connection_id
        self.is_local = is_local
        self.connection_id_gone = False
        self.aws_client: Optional[AWSAPIGatewayServiceClient] = None

    async def initialize_aws_client(self):
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
            AppLogger.log_warning(f"WebSocket connection {self.connection_id} closed")
        except Exception as e:
            AppLogger.log_error(f"Error pushing to WebSocket {self.connection_id}: {e}")

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
