import asyncio
from typing import Any, Dict, List

from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.ide_review.base_websocket_manager import BaseWebSocketManager
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    AgentTaskResult,
    RequestType,
    WebSocketMessage,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager import IdeReviewManager
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository
from deputydev_core.utils.app_logger import AppLogger


class MultiAgentWebSocketManager(BaseWebSocketManager):
    """
    Manages multi-agent websocket communication for extension review.
    Handles parallel agent execution and real-time result streaming.
    """

    def __init__(self, connection_id: str, review_id: int, is_local: bool = False):
        self.connection_id = connection_id
        self.review_id = review_id
        self.is_local = is_local
        self.connection_id_gone = False

        super().__init__(connection_id, is_local)

    async def execute_agent_task(self, agent_request: AgentRequestItem) -> AgentTaskResult:
        """
        Execute a single agent task using ExtensionReviewManager.review_diff.

        Args:
            agent_request: Individual agent request

        Returns:
            AgentTaskResult: Result of agent execution
        """
        try:
            formatted_result = await IdeReviewManager.review_diff(agent_request)
            return WebSocketMessage(**formatted_result)

        except Exception as e:
            AppLogger.log_error(f"Error executing agent task {agent_request.agent_id}: {e}")
            return WebSocketMessage(type="AGENT_FAIL", agent_id=agent_request.agent_id, data={"message": str(e)})

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
            return "AGENT_COMPLETE"
        elif result_type == "REVIEW_ERROR":
            return "AGENT_ERROR"
        else:
            return "AGENT_COMPLETE"

    async def process_request(self, agents: List[AgentRequestItem], local_testing_stream_buffer) -> None:
        """
        Process multiple agent requests in parallel and stream results.

        For single agent: runs directly
        For multiple agents: implements cache establishing/utilizing pattern

        Args:
            agents: List of agent requests to process
            local_testing_stream_buffer: Buffer for local testing streams
        """
        try:
            if len(agents) == 1:
                await self.execute_and_stream_agent(agents[0], local_testing_stream_buffer)
            else:
                await self._process_multiple_agents_with_cache_pattern(agents, local_testing_stream_buffer)

        except Exception as e:
            AppLogger.log_error(f"Error in process_multi_agent_request: {e}")
            await self.push_to_connection_stream(
                WebSocketMessage(type="AGENT_FAIL", data={"message": f"Agent processing error: {str(e)}"}),
                local_testing_stream_buffer,
            )
        finally:
            # Clean up AWS client
            if self.aws_client:
                await self.aws_client.close()

    async def _process_multiple_agents_with_cache_pattern(
        self, agents: List[AgentRequestItem], local_testing_stream_buffer
    ) -> None:
        """
        Process multiple agents using cache establishing/utilizing pattern.

        Cache establishing agents (SECURITY, CODE_MAINTAINABILITY) run first,
        followed by cache utilizing agents (all others).

        Args:
            agents: List of agent requests to process
            local_testing_stream_buffer: Buffer for local testing streams
        """
        try:
            agent_ids = [agent.agent_id for agent in agents]

            user_agents: List[UserAgentDTO] = await UserAgentRepository.db_get(
                filters={"id__in": agent_ids, "is_deleted": False}
            )

            if not user_agents:
                AppLogger.log_warn(f"No valid user agents found for IDs: {agent_ids}")
                return

            agent_id_to_name = {user_agent.id: user_agent.agent_name for user_agent in user_agents}

            cache_establishing_agents = []
            cache_utilizing_agents = []

            for agent_request in agents:
                agent_name = agent_id_to_name.get(agent_request.agent_id)

                if agent_name in [AgentTypes.SECURITY.value, AgentTypes.CODE_MAINTAINABILITY.value]:
                    cache_establishing_agents.append(agent_request)
                else:
                    cache_utilizing_agents.append(agent_request)

            if cache_establishing_agents:
                cache_establishing_tasks = [
                    asyncio.create_task(self.execute_and_stream_agent(agent, local_testing_stream_buffer))
                    for agent in cache_establishing_agents
                ]
                await asyncio.gather(*cache_establishing_tasks, return_exceptions=True)

            if cache_utilizing_agents:
                cache_utilizing_tasks = [
                    asyncio.create_task(self.execute_and_stream_agent(agent, local_testing_stream_buffer))
                    for agent in cache_utilizing_agents
                ]
                await asyncio.gather(*cache_utilizing_tasks, return_exceptions=True)

        except Exception as e:
            AppLogger.log_error(f"Error in _process_multiple_agents_with_cache_pattern: {e}")
            await self.push_to_connection_stream(
                WebSocketMessage(type="AGENT_FAIL", data={"message": f"Multi-agent processing error: {str(e)}"}),
                local_testing_stream_buffer,
            )

    async def execute_and_stream_agent(self, agent_request: AgentRequestItem, local_testing_stream_buffer) -> None:
        """
        Execute single agent and stream its result.

        Args:
            agent_request: Agent request to execute
        """
        try:
            if agent_request.type == RequestType.QUERY:
                await self.push_to_connection_stream(
                    WebSocketMessage(type="AGENT_START", agent_id=agent_request.agent_id), local_testing_stream_buffer
                )

            agent_ws_message = await self.execute_agent_task(agent_request)
            await self.push_to_connection_stream(agent_ws_message, local_testing_stream_buffer)

        except Exception as e:
            AppLogger.log_error(f"Error executing and streaming agent {agent_request.agent_id}: {e}")
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="AGENT_FAIL",
                    agent_id=agent_request.agent_id,
                    data={
                        "message": str(e),
                    },
                ),
                local_testing_stream_buffer,
            )
