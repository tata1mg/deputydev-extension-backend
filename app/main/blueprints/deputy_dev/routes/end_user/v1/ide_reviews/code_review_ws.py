import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

import aiohttp
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.error_codes import APIErrorCodes
from sanic import Blueprint, Websocket, response

from app.backend_common.caches.websocket_connections_cache import WebsocketConnectionCache
from app.backend_common.utils.sanic_wrapper import CONFIG, Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    MultiAgentReviewRequest,
    WebSocketMessage,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager import (
    IdeReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager import (
    MultiAgentWebSocketManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.post_proces_web_socket_manager import (
    PostProcessWebSocketManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.post_processors.ide_review_post_processor import (
    IdeReviewPostProcessor,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate, get_auth_data
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
    validate_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData

ide_review_websocket = Blueprint("ide_review_websocket", "")

config = CONFIG.config

local_testing_stream_buffer: Dict[str, List[str]] = {}


@ide_review_websocket.route("/legacy-run-agent", methods=["POST"])
@validate_client_version
@authenticate
async def run_extension_agent(request: Request, **kwargs: Any) -> ResponseDict | response.JSONResponse:
    """
    Run an agent for extension code review.

    Payload:
    - review_id: The review ID from pre-process step
    - agent_type: The type of agent to run (e.g., "PERFORMANCE_OPTIMIZATION", "SECURITY", etc.)
    - type: Request type ("query" for initial request, "tool_use_response" for tool responses)
    - tool_use_response: Tool use response data (required when type is "tool_use_response")

    Returns:
    - For query type: Either tool request details or final result
    - For tool_use_response type: Either next tool request or final result
    """
    agent_request = AgentRequestItem(**request.json)
    result = await IdeReviewManager.review_diff(agent_request)
    return send_response(result)


@ide_review_websocket.route("/legacy-post-process", methods=["POST"])
@validate_client_version
@authenticate
async def legacy_post_process(request: Request, **kwargs: Any) -> ResponseDict | response.JSONResponse:
    data = request.json
    processor = IdeReviewPostProcessor()
    await processor.post_process_pr(data, user_team_id=1)
    return send_response({"status": "SUCCESS"})


@ide_review_websocket.route("/run-agent", methods=["POST"])
async def run_multi_agent_review(_request: Request, **kwargs: Any) -> ResponseDict | response.JSONResponse:  # noqa: C901
    connection_id: str = _request.json["headers"].get("X-Amzn-ConnectionId")  # type: ignore
    is_local: bool = _request.json["headers"].get("X-Is-Local") == "true"

    connection_data = await WebsocketConnectionCache.get(connection_id)
    if connection_data is None:
        return send_response(
            {"status": "ERROR", "message": f"No connection data found for connection ID: {connection_id}"}
        )
    client_data = ClientData(**connection_data["client_data"])

    # Validate client version
    is_valid, upgrade_version, client_download_link = validate_version(
        client=client_data.client, client_version=client_data.client_version
    )
    if not is_valid:
        manager = MultiAgentWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.push_to_connection_stream(
            WebSocketMessage(
                type="AGENT_FAIL",
                data={
                    "error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value,
                    "upgrade_version": upgrade_version,
                    **({"client_download_link": client_download_link} if client_download_link else {}),
                },
            )
        )
        return send_response({"status": "INVALID_CLIENT_VERSION"})

    # Authenticate user (with fallback for local testing)
    auth_data: Optional[AuthData] = None
    auth_error: bool = False

    _request.headers["Authorization"] = f"""Bearer {_request.json["body"].get("auth_token", "")}"""
    _request.headers["X-Session-ID"] = str(_request.json["body"].get("session_id", ""))
    _request.headers["X-Session-Type"] = str(_request.json["body"].get("session_type", ""))

    try:
        auth_data, _ = await get_auth_data(_request)
    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Unable to Authenticate user: Error: {e}")
        auth_error = True
        auth_data = None

    if not is_local and (auth_error or not auth_data):
        manager = MultiAgentWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.push_to_connection_stream(
            WebSocketMessage(
                type="AGENT_FAIL", data={"message": "Unable to authenticate user", "status": "NOT_VERIFIED"}
            ),
            local_testing_stream_buffer,
        )
        return send_response({"status": "SESSION_EXPIRED"})

    try:
        payload_dict = _request.json["body"]
        if "connection_id" not in payload_dict:
            payload_dict["connection_id"] = connection_id

        if auth_data and not payload_dict.get("user_team_id"):
            payload_dict["user_team_id"] = auth_data.user_team_id

        multi_agent_request = MultiAgentReviewRequest(**payload_dict)
    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Invalid request payload: {e}")
        return send_response({"status": "ERROR", "message": f"Invalid request payload: {str(e)}"})

    async def process_multi_agent_review_task(request: MultiAgentReviewRequest, is_local: bool = False) -> None:
        """
        Background task to process multi-agent review requests.

        Args:
            request: Multi-agent review request
            is_local: Whether this is a local testing request
        """
        manager = None
        try:
            # Create WebSocket manager
            manager = MultiAgentWebSocketManager(request.connection_id, request.review_id, is_local)
            await manager.initialize_aws_client()

            # Process all agents
            await manager.process_request(request.agents, local_testing_stream_buffer)

        except Exception as e:  # noqa: BLE001
            AppLogger.log_error(f"Error in process_multi_agent_review_task: {e}")
            if manager:
                try:
                    await manager.push_to_connection_stream(
                        WebSocketMessage(type="AGENT_FAIL", data={"message": f"Background task error: {str(e)}"}),
                        local_testing_stream_buffer,
                    )
                except Exception as stream_error:  # noqa: BLE001
                    AppLogger.log_error(f"Error sending error message to stream: {stream_error}")

    # Create and start background processing task
    asyncio.create_task(process_multi_agent_review_task(multi_agent_request, is_local))

    return send_response({"status": "SUCCESS"})


@ide_review_websocket.websocket("/run-multi-agent-local-connection")
async def multi_agent_websocket_local(request: Request, ws: Websocket) -> None:
    """Local testing WebSocket endpoint for multi-agent review."""
    try:
        async with aiohttp.ClientSession() as session:
            # Generate random connection ID
            connection_id = uuid.uuid4().hex

            # Mock connection setup for local testing
            self_host_url = f"http://{ConfigManager.configs['HOST']}:{ConfigManager.configs['PORT']}"
            url = f"{self_host_url}/end_user/v1/websocket-connection/connect"

            headers: Dict[str, str] = {**dict(request.headers), "connectionid": connection_id}
            connection_response = await session.post(url, headers=headers)
            connection_data = await connection_response.json()

            if connection_data.get("status") != "SUCCESS":
                raise Exception("Connection failed")

            while True:
                try:
                    # Receive payload from WebSocket
                    raw_payload = await ws.recv()
                    payload = {"body": json.loads(raw_payload)}

                    # Add connection_id and mark as local
                    payload.setdefault("headers", {})["X-Amzn-ConnectionId"] = connection_id
                    payload["headers"]["X-Is-Local"] = "true"

                    # Send to multi-agent endpoint
                    await session.post(
                        f"{self_host_url}/end_user/v1/ide-reviews/run-agent",
                        headers={"connectionid": connection_id, "X-Is-Local": "true"},
                        json=payload,
                    )

                    # Stream results back to client
                    while True:
                        if local_testing_stream_buffer.get(connection_id):
                            data = local_testing_stream_buffer[connection_id].pop(0)
                            await ws.send(data)

                            # Check if stream ended
                            message_data = json.loads(data)
                            if message_data.get("type") == "STREAM_END":
                                del local_testing_stream_buffer[connection_id]
                                break
                        else:
                            await asyncio.sleep(0.2)

                except Exception as e:  # noqa: BLE001
                    AppLogger.log_error(f"Error in WebSocket connection: {e}")
                    break

    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error in multi-agent WebSocket connection: {e}")


@ide_review_websocket.route("/post-process", methods=["POST"])
async def post_process_extension_review(_request: Request, **kwargs: Any) -> ResponseDict | response.JSONResponse:
    connection_id: str = _request.json["headers"].get("X-Amzn-ConnectionId")  # type: ignore
    is_local: bool = _request.json["headers"].get("X-Is-Local") == "true"

    connection_data = await WebsocketConnectionCache.get(connection_id)
    if connection_data is None:
        return send_response(
            {"status": "ERROR", "message": f"No connection data found for connection ID: {connection_id}"}
        )
    client_data = ClientData(**connection_data["client_data"])

    # Validate client version
    is_valid, upgrade_version, client_download_link = validate_version(
        client=client_data.client, client_version=client_data.client_version
    )
    if not is_valid:
        manager = PostProcessWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.push_to_connection_stream(
            WebSocketMessage(
                type="STREAM_ERROR",
                data={
                    "error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value,
                    "upgrade_version": upgrade_version,
                },
            ),
            local_testing_stream_buffer,
        )
        return send_response({"status": "INVALID_CLIENT_VERSION"})

    # Authenticate user (with fallback for local testing)
    auth_data: Optional[AuthData] = None
    auth_error: bool = False

    _request.headers["Authorization"] = f"""Bearer {_request.json["body"].get("auth_token", "")}"""
    _request.headers["X-Session-ID"] = str(_request.json["body"].get("session_id", ""))
    _request.headers["X-Session-Type"] = str(_request.json["body"].get("session_type", ""))

    try:
        auth_data, _ = await get_auth_data(_request)
    except Exception:  # noqa: BLE001
        auth_error = True
        auth_data = None

    if not is_local and (auth_error or not auth_data):
        manager = PostProcessWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.push_to_connection_stream(
            WebSocketMessage(
                type="STREAM_ERROR", data={"message": "Unable to authenticate user", "status": "NOT_VERIFIED"}
            ),
            local_testing_stream_buffer,
        )
        return send_response({"status": "SESSION_EXPIRED"})

    try:
        payload_dict = _request.json["body"]
        if "connection_id" not in payload_dict:
            payload_dict["connection_id"] = connection_id

        if auth_data and not payload_dict.get("user_team_id"):
            payload_dict["user_team_id"] = auth_data.user_team_id

    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Invalid request payload: {e}")
        return send_response({"status": "ERROR", "message": f"Invalid request payload: {str(e)}"})

    # Create and start background processing task
    async def process_post_process_task() -> None:
        manager = PostProcessWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.process_post_process_task(payload_dict, local_testing_stream_buffer)

    asyncio.create_task(process_post_process_task())

    return send_response({"status": "SUCCESS"})


@ide_review_websocket.websocket("/post-process-local-connection")
async def post_process_websocket_local(request: Request, ws: Websocket) -> None:
    """Local testing WebSocket endpoint for post-process."""
    try:
        async with aiohttp.ClientSession() as session:
            # Generate random connection ID
            connection_id = uuid.uuid4().hex

            # Mock connection setup for local testing
            self_host_url = f"http://{ConfigManager.configs['HOST']}:{ConfigManager.configs['PORT']}"
            url = f"{self_host_url}/end_user/v1/websocket-connection/connect"

            headers: Dict[str, str] = {**dict(request.headers), "connectionid": connection_id}
            connection_response = await session.post(url, headers=headers)
            connection_data = await connection_response.json()

            if connection_data.get("status") != "SUCCESS":
                raise Exception("Connection failed")

            while True:
                try:
                    # Receive payload from WebSocket
                    raw_payload = await ws.recv()
                    payload = {"body": json.loads(raw_payload)}

                    # Add connection_id and mark as local
                    payload["connection_id"] = connection_id

                    # Add connection_id and mark as local
                    payload.setdefault("headers", {})["X-Amzn-ConnectionId"] = connection_id
                    payload["headers"]["X-Is-Local"] = "true"

                    # Send to post-process endpoint
                    await session.post(
                        f"{self_host_url}/end_user/v1/ide-reviews/post-process",
                        headers={"connectionid": connection_id, "X-Is-Local": "true"},
                        json=payload,
                    )

                    # Stream results back to client
                    while True:
                        if local_testing_stream_buffer.get(connection_id):
                            data = local_testing_stream_buffer[connection_id].pop(0)
                            await ws.send(data)

                            # Check if stream ended
                            message_data = json.loads(data)
                            if message_data.get("type") == "STREAM_END":
                                del local_testing_stream_buffer[connection_id]
                                break
                        else:
                            await asyncio.sleep(0.2)

                except Exception as e:  # noqa: BLE001
                    AppLogger.log_error(f"Error in WebSocket connection: {e}")
                    break

    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error in post-process WebSocket connection: {e}")
