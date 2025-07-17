import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from deputydev_core.utils.app_logger import AppLogger
from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    AWSAPIGatewayServiceClient,
    SocketClosedException,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.dataclass.main import (
    AgentRequestItem,
    AgentTaskResult,
    WebSocketMessage,
    RequestType,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.extension_review_manager import \
    ExtensionReviewManager
from deputydev_core.utils.config_manager import ConfigManager


class MultiAgentWebSocketManager:
    """
    Manages multi-agent websocket communication for extension review.
    Handles parallel agent execution and real-time result streaming.
    """

    def __init__(self, connection_id: str, is_local: bool = False):
        self.connection_id = connection_id
        self.is_local = is_local
        self.connection_id_gone = False
        self.aws_client: Optional[AWSAPIGatewayServiceClient] = None
        self.local_testing_stream_buffer: Dict[str, List[str]] = {}

    async def initialize_aws_client(self):
        """Initialize AWS WebSocket client."""
        if not self.is_local:
            self.aws_client = AWSAPIGatewayServiceClient()
            await self.aws_client.init_client(
                endpoint=f"{ConfigManager.configs['AWS_API_GATEWAY']['CODE_GEN_WEBSOCKET_WEBHOOK_ENDPOINT']}"
            )

    async def push_to_connection_stream(self, message: WebSocketMessage, local_testing_stream_buffer) -> None:
        """
        Push message to WebSocket connection.

        Args:
            message: WebSocket message to send
        """
        if self.connection_id_gone:
            return

        # Add timestamp to message
        message.timestamp = datetime.utcnow().isoformat()
        message_data = message.model_dump(mode="json")

        try:
            if self.is_local:
                # Local testing - use buffer
                local_testing_stream_buffer.setdefault(self.connection_id, []).append(
                    json.dumps(message_data)
                )
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

    async def execute_agent_task(self, agent_request: AgentRequestItem) -> AgentTaskResult:
        """
        Execute a single agent task using ExtensionReviewManager.review_diff.

        Args:
            agent_request: Individual agent request

        Returns:
            AgentTaskResult: Result of agent execution
        """
        try:
            # Convert AgentRequestItem to payload format expected by review_diff
            payload = {
                "agent_id": agent_request.agent_id,
                "review_id": agent_request.review_id,
                "repo_id": agent_request.repo_id,
                "session_id": agent_request.session_id,
                "type": agent_request.type.value,
            }

            # Add tool_use_response if present
            if agent_request.tool_use_response:
                payload["tool_use_response"] = {
                    "tool_name": agent_request.tool_use_response.tool_name,
                    "tool_use_id": agent_request.tool_use_response.tool_use_id,
                    "response": agent_request.tool_use_response.response,
                }

            # Call ExtensionReviewManager.review_diff directly
            formatted_result = await ExtensionReviewManager.review_diff(payload)

            # Determine status from formatted result
            event_type = self.determine_event_type(formatted_result)

            # Extract agent information from formatted result or use defaults
            agent_name = formatted_result.get("agent_name", "unknown")
            agent_type = formatted_result.get("agent_type", "unknown")
            tokens_data = formatted_result.get("tokens_data", {})
            model = formatted_result.get("model", "")
            display_name = formatted_result.get("display_name", "")
            error_message = None

            # Handle error case
            if formatted_result.get("status") == "ERROR":
                event_type = "REVIEW_ERROR"
                error_message = formatted_result.get("message", "Unknown error occurred")

            return AgentTaskResult(
                agent_id=agent_request.agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                status=event_type,
                result=formatted_result,
                tokens_data=tokens_data,
                model=model,
                display_name=display_name,
                error_message=error_message
            )

        except Exception as e:
            AppLogger.log_error(f"Error executing agent task {agent_request.agent_id}: {e}")
            return AgentTaskResult(
                agent_id=agent_request.agent_id,
                agent_name="unknown",
                agent_type="unknown",
                status="error",
                result={},
                error_message=str(e)
            )

    def determine_event_type(self, formatted_result: Dict[str, Any]) -> str:
        """
        Determine status from formatted agent result.

        Args:
            formatted_result: Formatted result from ExtensionReviewManager

        Returns:
            Status string: 'tool_use_request', 'success', or 'error'
        """
        if formatted_result.get("status") == "ERROR":
            return "AGENT_ERROR"

        result_type = formatted_result.get("type", "")
        if result_type == "TOOL_USE_REQUEST":
            return "TOOL_USE_REQUEST"
        elif result_type == "REVIEW_COMPLETE":
            return "REVIEW_COMPLETE"
        elif result_type == "REVIEW_ERROR":
            return "REVIEW_ERROR"
        else:
            return "REVIEW_COMPLETE"  # Default to success for other cases

    async def process_multi_agent_request(self, agents: List[AgentRequestItem], local_testing_stream_buffer) -> None:
        """
        Process multiple agent requests in parallel and stream results.

        Args:
            agents: List of agent requests to process
        """
        try:
            # Create tasks for all agents
            tasks = []
            for agent_request in agents:
                task = asyncio.create_task(
                    self._execute_and_stream_agent(agent_request, local_testing_stream_buffer)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful completions (exceptions won't be counted)
            successful_completions = sum(1 for result in completed_tasks if not isinstance(result, Exception))


        except Exception as e:
            AppLogger.log_error(f"Error in process_multi_agent_request: {e}")
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="STREAM_ERROR",
                    data={"message": f"Multi-agent processing error: {str(e)}"}
                ), local_testing_stream_buffer
            )
        finally:
            # Clean up AWS client
            if self.aws_client:
                await self.aws_client.close()

    async def _execute_and_stream_agent(self, agent_request: AgentRequestItem, local_testing_stream_buffer) -> None:
        """
        Execute single agent and stream its result.

        Args:
            agent_request: Agent request to execute
        """
        try:
            if agent_request.type == RequestType.QUERY:
                await self.push_to_connection_stream(
                    WebSocketMessage(
                        type="AGENT_START",
                        agent_id=agent_request.agent_id
                    ), local_testing_stream_buffer
                )

            # Execute agent task using review_diff
            result = await self.execute_agent_task(agent_request)

            # Stream the result
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type=result.status,
                    agent_id=result.agent_id,
                    data=result.model_dump(mode="json")
                ), local_testing_stream_buffer
            )

        except Exception as e:
            AppLogger.log_error(f"Error executing and streaming agent {agent_request.agent_id}: {e}")
            # Stream error result
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="AGENT_FAIL",
                    agent_id=agent_request.agent_id,
                    data={
                        "agent_id": agent_request.agent_id,
                        "status": "error",
                        "error_message": str(e),
                        "result": {}
                    }
                ), local_testing_stream_buffer
            )

    def get_local_stream_data(self) -> List[str]:
        """Get local stream data for testing."""
        return self.local_testing_stream_buffer.get(self.connection_id, [])

    def clear_local_stream_data(self) -> None:
        """Clear local stream data for testing."""
        if self.connection_id in self.local_testing_stream_buffer:
            del self.local_testing_stream_buffer[self.connection_id]
