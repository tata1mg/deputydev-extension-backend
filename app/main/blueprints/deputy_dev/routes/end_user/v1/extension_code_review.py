import asyncio
import json

from deputydev_core.utils.constants.error_codes import APIErrorCodes
from sanic import Blueprint
from torpedo import CONFIG, Request, send_response
from typing import Optional, Dict, List

from app.backend_common.caches.websocket_connections_cache import WebsocketConnectionCache
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository
from app.main.blueprints.one_dev.utils.authenticate import authenticate, get_auth_data
from app.main.blueprints.deputy_dev.services.code_review.extension_review.managers.extension_code_review_history_manager import (
    ExtensionCodeReviewHistoryManager,
)
from app.backend_common.utils.wrapper import exception_logger
from app.main.blueprints.deputy_dev.services.code_review.extension_review.pre_processors.extension_review_pre_processor import (
    ExtensionReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.post_processors.extension_review_post_processor import (
    ExtensionReviewPostProcessor,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version, validate_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.models.ide_review_history_params import ReviewHistoryParams
from app.main.blueprints.deputy_dev.services.code_review.extension_review.extension_review_manager import (
    ExtensionReviewManager,
)
from deputydev_core.utils.app_logger import AppLogger
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.services.code_review.extension_review.extension_multi_agent_review_manager import MultiAgentWebSocketManager

from app.main.blueprints.one_dev.utils.session import get_valid_session_data
from app.main.blueprints.deputy_dev.services.code_review.extension_review.dataclass.main import WebSocketMessage, \
    MultiAgentReviewRequest, AgentRequestItem
from app.main.blueprints.deputy_dev.services.code_review.extension_review.post_proces_web_socket_manager import PostProcessWebSocketManager
from app.main.blueprints.deputy_dev.services.code_review.extension_review.dataclass.main import CommentUpdateRequest, GetRepoIdRequest
from app.main.blueprints.deputy_dev.services.repository.ide_review_comment_feedbacks.repository import (
    IdeReviewCommentFeedbacksRepository,
)
from app.main.blueprints.deputy_dev.services.repository.extension_review_feedbacks.repository import (
    ExtensionReviewFeedbacksRepository,
)
from app.main.blueprints.deputy_dev.models.dto.ide_review_comment_feedback_dto import IdeReviewCommentFeedbackDTO
from app.main.blueprints.deputy_dev.models.dto.extension_review_feedback_dto import ExtensionReviewFeedbackDTO

extension_code_review = Blueprint("ide_code_review", "/extension-code-review")

config = CONFIG.config

local_testing_stream_buffer: Dict[str, List[str]] = {}


@extension_code_review.route("/history", methods=["GET"])
@validate_client_version
@authenticate
async def code_review_history(_request: Request, auth_data: AuthData, **kwargs):
    """
    Get code review history based on filters
    Query parameters:
    - user_team_id: Filter by user team ID
    - source_branch: Filter by source branch
    - target_branch: Filter by target branch
    - repo_id: Filter by repository ID
    """
    try:
        # Extract query parameters
        query_params = _request.request_params()
        review_history_params = ReviewHistoryParams(**query_params, user_team_id=auth_data.user_team_id)

        # Initialize manager and fetch reviews
        history_manager = ExtensionCodeReviewHistoryManager()
        reviews = await history_manager.fetch_reviews_by_filters(review_history_params)
        return send_response(reviews)

    except Exception as e:
        raise e


@extension_code_review.route("/pre-process", methods=["POST"])
@validate_client_version
@authenticate
async def pre_process_extension_review(request: Request, auth_data: AuthData, **kwargs):
    try:
        data = request.json
        processor = ExtensionReviewPreProcessor()
        review_dto = await processor.pre_process_pr(
            data,
            user_team_id=auth_data.user_team_id,
            )
        return send_response(review_dto)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


@extension_code_review.route("/run-agent", methods=["POST"])
@validate_client_version
@authenticate
async def run_extension_agent(request: Request, **kwargs):
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
    result = await ExtensionReviewManager.review_diff(agent_request)
    return send_response(result)



@extension_code_review.route("/legacy-post-process", methods=["POST"])
@validate_client_version
@authenticate
async def legacy_post_process(request: Request, **kwargs):
    data = request.json
    processor = ExtensionReviewPostProcessor()
    await processor.post_process_pr(data, user_team_id=1)
    return send_response({"status": "SUCCESS"})


@extension_code_review.route("/run-multi-agent", methods=["POST"])
async def run_multi_agent_review(_request: Request, **kwargs):
    connection_id: str = _request.headers.get("connectionid")  # type: ignore
    is_local: bool = _request.headers.get("X-Is-Local") == "true"

    connection_data = await WebsocketConnectionCache.get(connection_id)
    if connection_data is None:
        return send_response({
            "status": "ERROR",
            "message": f"No connection data found for connection ID: {connection_id}"
        })
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
                }
            )
        )
        return send_response({"status": "INVALID_CLIENT_VERSION"})

    # Authenticate user (with fallback for local testing)
    auth_data: Optional[AuthData] = None
    auth_error: bool = False

    _request.headers["Authorization"] = f"""Bearer {_request.json.get("auth_token", "")}"""
    _request.headers["X-Session-ID"] = str(_request.json.get("session_id", ""))
    _request.headers["X-Session-Type"] = str(_request.json.get("session_type", ""))

    try:
        auth_data, _ = await get_auth_data(_request)
    except Exception:  # noqa: BLE001
        auth_error = True
        auth_data = None



    if not is_local and (auth_error or not auth_data):
        manager = MultiAgentWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.push_to_connection_stream(
            WebSocketMessage(
                type="AGENT_FAIL",
                data={"message": "Unable to authenticate user", "status": "NOT_VERIFIED"}
            )
        )
        return send_response({"status": "SESSION_EXPIRED"})

    try:
        payload_dict = _request.json
        if "connection_id" not in payload_dict:
            payload_dict["connection_id"] = connection_id

        if auth_data and not payload_dict.get("user_team_id"):
            payload_dict["user_team_id"] = auth_data.user_team_id


        multi_agent_request = MultiAgentReviewRequest(**payload_dict)
    except Exception as e:
        AppLogger.log_error(f"Invalid request payload: {e}")
        return send_response({
            "status": "ERROR",
            "message": f"Invalid request payload: {str(e)}"
        })

    async def process_multi_agent_review_task(
            request: MultiAgentReviewRequest,
            is_local: bool = False
    ) -> None:
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

        except Exception as e:
            AppLogger.log_error(f"Error in process_multi_agent_review_task: {e}")
            if manager:
                try:
                    await manager.push_to_connection_stream(
                        WebSocketMessage(
                            type="AGENT_FAIL",
                            data={"message": f"Background task error: {str(e)}"}
                        ),
                        local_testing_stream_buffer
                    )
                except Exception as stream_error:
                    AppLogger.log_error(f"Error sending error message to stream: {stream_error}")

    # Create and start background processing task
    asyncio.create_task(
        process_multi_agent_review_task(multi_agent_request, is_local)
    )

    return send_response({"status": "SUCCESS"})



@extension_code_review.websocket("/run-multi-agent-local-connection")
async def multi_agent_websocket_local(request: Request, ws) -> None:
    """Local testing WebSocket endpoint for multi-agent review."""
    try:
        import uuid
        import aiohttp
        from deputydev_core.utils.config_manager import ConfigManager

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
                    payload = json.loads(raw_payload)

                    # Add connection_id and mark as local
                    payload["connection_id"] = connection_id

                    # Send to multi-agent endpoint
                    await session.post(
                        f"{self_host_url}/end_user/v1/extension-code-review/run-multi-agent",
                        headers={"connectionid": connection_id, "X-Is-Local": "true"},
                        json=payload,
                    )

                    # Stream results back to client
                    while True:
                        if local_testing_stream_buffer.get(connection_id):
                            data = local_testing_stream_buffer[connection_id].pop(0)
                            print("WS Data: ", data)
                            await ws.send(data)

                            # Check if stream ended
                            message_data = json.loads(data)
                            if message_data.get("type") == "STREAM_END":
                                del local_testing_stream_buffer[connection_id]
                                break
                        else:
                            await asyncio.sleep(0.2)

                except Exception as e:
                    AppLogger.log_error(f"Error in WebSocket connection: {e}")
                    break

    except Exception as e:
        AppLogger.log_error(f"Error in multi-agent WebSocket connection: {e}")

@extension_code_review.route("/post-process", methods=["POST"])
async def post_process_extension_review(_request: Request, **kwargs):
    connection_id: str = _request.headers.get("connectionid")  # type: ignore
    is_local: bool = _request.headers.get("X-Is-Local") == "true"

    connection_data = await WebsocketConnectionCache.get(connection_id)
    if connection_data is None:
        return send_response({
            "status": "ERROR",
            "message": f"No connection data found for connection ID: {connection_id}"
        })
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
                }
            ),
            local_testing_stream_buffer
        )
        return send_response({"status": "INVALID_CLIENT_VERSION"})

    # Authenticate user (with fallback for local testing)
    auth_data: Optional[AuthData] = None
    auth_error: bool = False

    _request.headers["Authorization"] = f"""Bearer {_request.json.get("auth_token", "")}"""
    _request.headers["X-Session-ID"] = str(_request.json.get("session_id", ""))
    _request.headers["X-Session-Type"] = str(_request.json.get("session_type", ""))

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
                type="STREAM_ERROR",
                data={"message": "Unable to authenticate user", "status": "NOT_VERIFIED"}
            ),
            local_testing_stream_buffer
        )
        return send_response({"status": "SESSION_EXPIRED"})

    try:
        payload_dict = _request.json
        if "connection_id" not in payload_dict:
            payload_dict["connection_id"] = connection_id

        if auth_data and not payload_dict.get("user_team_id"):
            payload_dict["user_team_id"] = auth_data.user_team_id

    except Exception as e:
        AppLogger.log_error(f"Invalid request payload: {e}")
        return send_response({
            "status": "ERROR",
            "message": f"Invalid request payload: {str(e)}"
        })

    # Create and start background processing task
    async def process_post_process_task():
        manager = PostProcessWebSocketManager(connection_id, is_local)
        await manager.initialize_aws_client()
        await manager.process_post_process_task(payload_dict, local_testing_stream_buffer)

    asyncio.create_task(process_post_process_task())

    return send_response({"status": "SUCCESS"})



@extension_code_review.websocket("/post-process-local-connection")
async def post_process_websocket_local(request: Request, ws) -> None:
    """Local testing WebSocket endpoint for post-process."""
    try:
        import uuid
        import aiohttp
        from deputydev_core.utils.config_manager import ConfigManager

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
                    payload = json.loads(raw_payload)

                    # Add connection_id and mark as local
                    payload["connection_id"] = connection_id

                    # Send to post-process endpoint
                    await session.post(
                        f"{self_host_url}/end_user/v1/extension-code-review/post-process",
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

                except Exception as e:
                    AppLogger.log_error(f"Error in WebSocket connection: {e}")
                    break

    except Exception as e:
        AppLogger.log_error(f"Error in post-process WebSocket connection: {e}")


@extension_code_review.route("/generate-comment-fix-query", methods=["GET"])
@validate_client_version
@authenticate
async def generate_comment_fix_query(request: Request, auth_data: AuthData, **kwargs):
    """
    Generate a query to fix a specific comment in the code review.

    Query parameters:
    - comment_id: The ID of the comment to fix
    """
    try:
        query_params = request.request_params()
        comment_id = query_params.get("comment_id")
        if not comment_id:
            raise ValueError("Missing required parameters: comment_id")

        # Generate the fix query
        manager = ExtensionReviewManager()
        fix_query = await manager.generate_comment_fix_query(comment_id=comment_id)
        return send_response({"fix_query": fix_query})
    except Exception as e:
        AppLogger.log_error(f"Error generating fix query: {e}")
        return send_response({"status": "ERROR", "message": str(e)})


@extension_code_review.route("/cancel_review", methods=["GET"])
@validate_client_version
@authenticate
async def cancel_review(request: Request, auth_data: AuthData, **kwargs):
    """
    Generate a query to fix a specific comment in the code review.

    Query parameters:
    - comment_id: The ID of the comment to fix
    """
    try:
        query_params = request.request_params()
        review_id = query_params.get("review_id")
        if not review_id:
            raise ValueError("Missing required parameters: review_id")

        # Generate the fix query
        manager = ExtensionReviewManager()
        data = await manager.cancel_review(review_id=review_id)
        return send_response(data)
    except Exception as e:
        AppLogger.log_error(f"Error generating fix query: {e}")
        return send_response({"status": "ERROR", "message": str(e)})


@extension_code_review.route("/update-comment-status", methods=["POST"])
@validate_client_version
@authenticate
async def update_comment_status(request: Request, auth_data: AuthData, **kwargs):
    """
    Generate a query to fix a specific comment in the code review.

    Query parameters:
    - comment_id: The ID of the comment to fix
    """
    try:
        query_params = request.request_params()
        comment_id = query_params.get("comment_id")
        status = query_params.get("status")
        comment_update_request = CommentUpdateRequest(id=comment_id, comment_status=status)
        if not comment_id:
            raise ValueError("Missing required parameters: comment_id")

        # Generate the fix query
        manager = ExtensionCodeReviewHistoryManager()
        data = await manager.update_comment_status(comment_update_request)
        return send_response(data)
    except Exception as e:
        AppLogger.log_error(f"Error updating comment status: {e}")
        return send_response({"status": "ERROR", "message": str(e)})


@extension_code_review.route("/get-repo-id", methods=["GET"])
@validate_client_version
@authenticate
async def get_repo_id(request: Request, auth_data: AuthData, **kwargs):
    try:
        query_params = request.request_params()
        data = GetRepoIdRequest(**query_params)
        processor = ExtensionReviewPreProcessor()
        repo_dto = await processor.get_repo_id(data, auth_data.user_team_id)
        return send_response({"repo_id": repo_dto.id})
    except Exception as e:
        AppLogger.log_error(f"Error getting repo id: {e}")
        return send_response({"status": "ERROR", "message": str(e)})


@extension_code_review.route("/comments/<comment_id:int>/feedback", methods=["POST"])
@validate_client_version
@authenticate
@exception_logger
async def create_comment_feedback(request: Request, auth_data: AuthData, comment_id: int, **kwargs):
    """
    Create feedback for a specific comment

    Request Body:
    {
        "feedback_comment": "string (optional)",
        "like": "boolean (optional)"
    }
    """
    try:
        # Get request body
        request_data = request.json or {}

        # Create feedback DTO
        feedback_dto = IdeReviewCommentFeedbackDTO(
            comment_id=comment_id,
            feedback_comment=request_data.get("feedback_comment"),
            like=request_data.get("like")
        )

        # Insert feedback via repository
        created_feedback = await IdeReviewCommentFeedbacksRepository.db_insert(feedback_dto)

        return send_response(created_feedback.model_dump(mode="json"))

    except Exception as e:
        raise e


@extension_code_review.route("/reviews/<review_id:int>/feedback", methods=["POST"])
@validate_client_version
@authenticate
@exception_logger
async def create_review_feedback(request: Request, auth_data: AuthData, review_id: int, **kwargs):
    """
    Create feedback for a specific review

    Request Body:
    {
        "feedback_comment": "string (optional)",
        "like": "boolean (optional)"
    }
    """
    try:
        # Get request body
        request_data = request.json or {}

        # Create feedback DTO
        feedback_dto = ExtensionReviewFeedbackDTO(
            review_id=review_id,
            feedback_comment=request_data.get("feedback_comment"),
            like=request_data.get("like")
        )

        # Insert feedback via repository
        created_feedback = await ExtensionReviewFeedbacksRepository.db_insert(feedback_dto)

        return send_response(created_feedback.model_dump(mode="json"))

    except Exception as e:
        raise e