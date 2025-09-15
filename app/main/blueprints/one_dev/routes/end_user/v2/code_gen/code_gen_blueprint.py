import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

import aiohttp
from deputydev_core.exceptions.exceptions import InputTokenLimitExceededError
from deputydev_core.exceptions.llm_exceptions import (
    LLMThrottledError,
)
from deputydev_core.llm_handler.dataclasses.main import StreamingEventType
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.error_codes import APIErrorCodes
from sanic import Blueprint, response
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.caches.code_gen_tasks_cache import (
    CodeGenTasksCache,
)
from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    AWSAPIGatewayServiceClient,
    SocketClosedError,
)
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.utils.authenticate import authenticate, get_auth_data
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.one_dev.services.migration.migration_manager import MessageThreadMigrationManager
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
    QuerySolverInput,
    StreamErrorData,
    TerminalCommandEditInput,
    UserQueryEnhancerInput,
)
from app.main.blueprints.one_dev.services.query_solver.inline_editor import (
    InlineEditGenerator,
)
from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver
from app.main.blueprints.one_dev.services.query_solver.terminal_command_editor import (
    TerminalCommandEditGenerator,
)
from app.main.blueprints.one_dev.services.query_solver.user_query_enhancer import (
    UserQueryEnhancer,
)
from app.main.blueprints.one_dev.utils.cancellation_checker import CancellationChecker
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
    validate_version,
)
from app.main.blueprints.one_dev.utils.session import (
    ensure_session_id,
    get_valid_session_data,
)


def get_model_display_name(model_name: str) -> str:
    """Get the display name for a model from the configuration."""
    try:
        chat_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
        for model in chat_models:
            if model.get("name") == model_name:
                return model.get("display_name", model_name)
        return model_name
    except Exception:  # noqa : BLE001
        return model_name


code_gen_v2_bp = Blueprint("code_gen_v2_bp", url_prefix="/code-gen")

local_testing_stream_buffer: Dict[str, List[str]] = {}


@code_gen_v2_bp.route("/generate-code-non-stream", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def solve_user_query_non_stream(  # noqa: C901
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    payload = QuerySolverInput(**_request.json, session_id=session_id)
    AppLogger.log_info(f"Starting new non-stream query for session {session_id}")
    # Store the active query and LLM model for potential cancellation
    session_data = {}
    if payload.query:
        session_data["query"] = payload.query
    if payload.llm_model:
        session_data["llm_model"] = payload.llm_model.value
    if session_data:
        await CodeGenTasksCache.set_session_data(session_id, session_data)
    blocks: List[Dict[str, Any]] = []
    # Add stream start block
    start_data = {"type": "STREAM_START"}
    if auth_data.session_refresh_token:
        start_data["new_session_data"] = auth_data.session_refresh_token
    blocks.append(start_data)

    # Create a task for this non-streaming request too for potential cancellation
    async def solve_query_task() -> List[Dict[str, Any]]:
        try:
            try:
                data = await QuerySolver().solve_query(payload=payload, client_data=client_data)
                last_block = None
                async for data_block in data:
                    last_block = data_block
                    blocks.append(data_block.model_dump(mode="json"))
                if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
                    blocks.append({"type": "QUERY_COMPLETE"})
                    await CodeGenTasksCache.cleanup_session_data(session_id)
                blocks.append({"type": "STREAM_END"})
            except asyncio.CancelledError:
                blocks.append({"type": "STREAM_CANCELLED", "message": "LLM processing cancelled"})
                raise
            except Exception as ex:  # noqa: BLE001
                AppLogger.log_error(f"Error in solving query: {ex}")
                blocks.append({"type": "STREAM_ERROR", "message": str(ex)})
        except Exception as e:  # noqa: BLE001
            AppLogger.log_error(f"Error in solving query: {e}")
        return blocks

    # Create and execute task without global tracking
    task = asyncio.create_task(solve_query_task())
    try:
        blocks = await task
    except asyncio.CancelledError:
        blocks.append({"type": "STREAM_CANCELLED", "message": "LLM processing cancelled"})
    except Exception as ex:  # noqa: BLE001
        AppLogger.log_error(f"Error in solving query: {ex}")
        blocks.append({"type": "STREAM_ERROR", "message": str(ex)})
    return send_response({"status": "SUCCESS", "blocks": blocks})


@code_gen_v2_bp.route("/generate-code", methods=["POST"])
async def solve_user_query(_request: Request, **kwargs: Any) -> ResponseDict | response.JSONResponse:  # noqa: C901
    connection_id: str = _request.headers["connectionid"]  # type: ignore
    connection_data: Any = await WebsocketConnectionCache.get(connection_id)
    if connection_data is None:
        raise ValueError(f"No connection data found for connection ID: {connection_id}")
    client_data = ClientData(**connection_data["client_data"])
    auth_error: bool
    auth_data: Optional[AuthData] = None
    _request.headers["Authorization"] = f"""Bearer {_request.json.get("auth_token", "")}"""
    _request.headers["X-Session-ID"] = str(_request.json.get("session_id", ""))
    _request.headers["X-Session-Type"] = str(_request.json.get("session_type", ""))
    auth_data: Optional[AuthData] = None
    auth_error: bool = False
    try:
        auth_data, _ = await get_auth_data(_request)
    except Exception:  # noqa: BLE001
        auth_error = True
        auth_data = None
    if auth_data:
        session_data = await get_valid_session_data(_request, client_data, auth_data, auto_create=True)
        _request.json["session_id"] = session_data.id
    is_local: bool = _request.headers.get("X-Is-Local") == "true"
    connection_id_gone = False
    aws_client = AWSAPIGatewayServiceClient()
    await aws_client.init_client(
        endpoint=f"{ConfigManager.configs['AWS_API_GATEWAY']['CODE_GEN_WEBSOCKET_WEBHOOK_ENDPOINT']}",
    )

    async def push_to_connection_stream(data: Dict[str, Any]) -> None:
        nonlocal connection_id
        nonlocal is_local
        nonlocal connection_id_gone
        nonlocal aws_client

        if not connection_id_gone:
            if is_local:
                local_testing_stream_buffer.setdefault(connection_id, []).append(json.dumps(data))
            else:
                try:
                    await aws_client.post_to_connection(
                        connection_id=connection_id,
                        message=json.dumps(data),
                    )
                except SocketClosedError:
                    connection_id_gone = True

    is_valid, upgrade_version, client_download_link = validate_version(
        client=client_data.client, client_version=client_data.client_version
    )
    if not is_valid:
        error_data = StreamErrorData(
            type="STREAM_ERROR",
            message={
                "error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value,
                "upgrade_version": upgrade_version,
                **({"client_download_link": client_download_link} if client_download_link else {}),
            },
            status="INVALID_CLIENT_VERSION",
        )
        await push_to_connection_stream(error_data.model_dump(mode="json"))
        return send_response({"status": "INVALID_CLIENT_VERSION"})
    if auth_error or not auth_data:
        error_data = {"type": "STREAM_ERROR", "message": "Unable to authenticate user", "status": "NOT_VERIFIED"}
        await push_to_connection_stream(error_data)
        return send_response({"status": "SESSION_EXPIRED"})
    user_team_id = auth_data.user_team_id
    payload_dict = _request.json
    if payload_dict.get("type") == "PAYLOAD_ATTACHMENT" and payload_dict.get("attachment_id"):
        attachment_id = payload_dict["attachment_id"]
        # 1. Lookup attachment
        attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)
        if not attachment_data or getattr(attachment_data, "status", None) == "deleted":
            raise ValueError(f"Attachment with ID {attachment_id} not found or already deleted.")
        s3_key = attachment_data.s3_key
        # 2. Fetch & decode S3 payload
        try:
            object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)
            s3_payload = json.loads(object_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode JSON payload from S3 for attachment {attachment_id}: {e}")

        # 3. Merge session fields from envelope (envelope wins)
        for field in ("session_id", "session_type", "auth_token"):
            if field in payload_dict:
                s3_payload[field] = payload_dict[field]
        payload_dict = s3_payload
        # 4. Delete S3 file and update DB (best effort; won't block downstream even if fails)
        try:
            await ChatFileUpload.delete_file_by_s3_key(s3_key=s3_key)
        except Exception:  # noqa: BLE001
            AppLogger.log_error(f"Failed to delete S3 file {s3_key} after fetching S3 payload.")
            pass
        try:
            await ChatAttachmentsRepository.update_attachment_status(
                attachment_id=attachment_id,
                status="deleted",
            )
        except Exception:  # noqa: BLE001
            AppLogger.log_error(f"Failed to delete attachment {attachment_id} after fetching S3 payload.")
            pass
    payload = QuerySolverInput(
        **payload_dict,
        user_team_id=user_team_id,
    )
    # HACK: Prevent cancellation of newer query for session_id
    # TODO: Cancellation shall be on query_id instead of session_id
    await CodeGenTasksCache.cleanup_session_data(payload.session_id)

    # Store the active query and LLM model for potential cancellation
    session_data = {}
    if payload.query:
        session_data["query"] = payload.query
        if payload.llm_model:
            session_data["llm_model"] = payload.llm_model.value
        if session_data:
            await CodeGenTasksCache.set_session_data(payload.session_id, session_data)

    async def solve_query() -> None:  # noqa : C901
        nonlocal payload
        nonlocal connection_id
        nonlocal client_data
        task_checker = CancellationChecker(payload.session_id)
        try:
            await task_checker.start_monitoring()
            # push stream start message
            start_data = {"type": "STREAM_START"}
            if auth_data.session_refresh_token:
                start_data["new_session_data"] = auth_data.session_refresh_token
            await push_to_connection_stream(start_data)
            data = await QuerySolver().solve_query(
                payload=payload, client_data=client_data, save_to_redis=True, task_checker=task_checker
            )
            last_block = None
            # push data to stream
            async for data_block in data:
                # Check if task was cancelled via Redis checker

                last_block = data_block
                await push_to_connection_stream(data_block.model_dump(mode="json"))

            # TODO: Sugar code this part
            if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
                query_end_data = {"type": "QUERY_COMPLETE"}
                await CodeGenTasksCache.cleanup_session_data(payload.session_id)
                await push_to_connection_stream(query_end_data)
            # push stream end message
            end_data = {"type": "STREAM_END"}
            await push_to_connection_stream(end_data)

        except LLMThrottledError as ex:
            AppLogger.log_error(
                f"Throttled by LLM provider: {getattr(ex, 'provider', None)} | "
                f"model: {getattr(ex, 'model', None)} | "
                f"detail: {ex.detail}"
            )
            error_data: Dict[str, Any] = {
                "type": "STREAM_ERROR",
                "status": "LLM_THROTTLED",
                "provider": getattr(ex, "provider", None),
                "model": getattr(ex, "model", None),
                "retry_after": ex.retry_after,
                "message": "This chat is currently being throttled. You can wait, or switch to a different model.",
                "detail": ex.detail,
                "region": getattr(ex, "region", None),
            }
            await push_to_connection_stream(error_data)

        except InputTokenLimitExceededError as ex:
            AppLogger.log_error(
                f"Input token limit exceeded: model={ex.model_name}, tokens={ex.current_tokens}/{ex.max_tokens}"
            )

            # Get available models with higher token limits
            better_models: List[Dict[str, Any]] = []

            try:
                code_gen_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
                llm_models_config = ConfigManager.configs.get("LLM_MODELS", {})
                current_model_limit = ex.max_tokens

                for model in code_gen_models:
                    model_name = model.get("name")
                    if model_name and model_name != ex.model_name and model_name in llm_models_config:
                        model_config = llm_models_config[model_name]
                        model_token_limit = model_config.get("INPUT_TOKENS_LIMIT", 100000)

                        if model_token_limit > current_model_limit:
                            enhanced_model = model.copy()
                            enhanced_model["input_token_limit"] = model_token_limit
                            better_models.append(enhanced_model)

                # Sort by token limit (highest first)
                better_models.sort(key=lambda m: m.get("input_token_limit", 0), reverse=True)

            except Exception as model_error:  # noqa : BLE001
                AppLogger.log_error(f"Error fetching better models: {model_error}")
            error_data: Dict[str, Any] = {
                "type": "STREAM_ERROR",
                "status": "INPUT_TOKEN_LIMIT_EXCEEDED",
                "model": ex.model_name,
                "current_tokens": ex.current_tokens,
                "max_tokens": ex.max_tokens,
                "query": payload.query,
                "message": f"Your message exceeds the context window supported by {get_model_display_name(ex.model_name)}. Try switching to a model with a higher context window to proceed.",
                "detail": ex.detail,
                "better_models": better_models,
            }

            await push_to_connection_stream(error_data)

        except asyncio.CancelledError as ex:
            cancel_data = {"type": "STREAM_ERROR", "message": f"LLM processing error: {str(ex)}"}
            await push_to_connection_stream(cancel_data)
        except Exception as ex:  # noqa: BLE001
            AppLogger.log_error(f"Error in solving query: {ex}")
            # push error message to stream
            error_data = {"type": "STREAM_ERROR", "message": f"LLM processing error: {str(ex)}"}
            await push_to_connection_stream(error_data)
        finally:
            await task_checker.stop_monitoring()
            await aws_client.close()

    asyncio.create_task(solve_query())
    return send_response({"status": "SUCCESS"})


@code_gen_v2_bp.route("/generate-enhanced-user-query", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_enhanced_user_query(
    _request: Request, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    input_data = UserQueryEnhancerInput(**_request.json, session_id=session_id)

    result = await UserQueryEnhancer().get_enhanced_user_query(
        payload=input_data,
    )

    return send_response(result, headers=kwargs.get("response_headers"))


@code_gen_v2_bp.route("/generate-inline-edit", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_inline_edit(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    data = await InlineEditGenerator().create_and_start_job(
        payload=InlineEditInput(**_request.json, session_id=session_id, auth_data=auth_data),
        client_data=client_data,
    )
    return send_response({"job_id": data, "session_id": session_id})


@code_gen_v2_bp.route("/terminal-command-edit", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def terminal_command_edit(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    input_data = TerminalCommandEditInput(**_request.json, session_id=session_id, auth_data=auth_data)
    result = await TerminalCommandEditGenerator().get_new_terminal_command(
        payload=input_data,
        client_data=client_data,
    )
    return send_response(result)


@code_gen_v2_bp.route("/cancel", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def cancel_chat(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    await CodeGenTasksCache.cancel_session(session_id)
    return send_response(
        {
            "status": "SUCCESS",
            "message": "LLM processing cancelled successfully ",
            "cancelled_session_id": session_id,
        }
    )


# This is for testing purposes only
# This mocks the AWS api gateway connection


@code_gen_v2_bp.websocket("/generate-code-local-connection")
async def sse_websocket(request: Request, ws: Any) -> None:
    try:
        async with aiohttp.ClientSession() as session:
            # generate a random connectionid
            connection_id = uuid.uuid4().hex
            # first mock connecting to the server using /connect endpoint
            self_host_url = f"http://{ConfigManager.configs['HOST']}:{ConfigManager.configs['PORT']}"
            url = f"{self_host_url}/end_user/v1/websocket-connection/connect"

            # Convert starlette request headers to dict
            headers: Dict[str, str] = {**dict(request.headers), "connectionid": connection_id}

            connection_response = await session.post(url, headers=headers)
            connection_data = await connection_response.json()
            if connection_data.get("status") != "SUCCESS":
                raise Exception("Connection failed")

            while True:
                try:
                    # now receive the data
                    raw_payload = await ws.recv()
                    payload = json.loads(raw_payload)

                    # then get a stream of data from the /generate-code endpoint
                    await session.post(
                        f"{self_host_url}/end_user/v2/code-gen/generate-code",
                        headers={"connectionid": connection_id, "X-Is-Local": "true"},
                        json=payload,
                    )

                    # iterate over message response and send the data to the client
                    while True:
                        if local_testing_stream_buffer.get(connection_id):
                            data = local_testing_stream_buffer[connection_id].pop(0)
                            await ws.send(data)
                            if data == json.dumps({"type": "STREAM_END"}):
                                # remove the connectionid from stream buffer
                                del local_testing_stream_buffer[connection_id]
                                break
                        else:
                            await asyncio.sleep(0.2)
                except Exception as e:  # noqa: BLE001
                    AppLogger.log_error(f"Error in websocket connection: {e}")
                    break

    except Exception as _ex:  # noqa: BLE001
        AppLogger.log_error(f"Error in websocket connection: {_ex}")


@code_gen_v2_bp.websocket("/generate-code-ws")
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def solve_user_query_ws(_request: Request, ws: WebsocketImplProtocol, **kwargs: Any) -> None:  # noqa: C901
    client_data: ClientData = kwargs.get("client_data")
    auth_data: AuthData = kwargs.get("auth_data")
    session_id: int = kwargs.get("session_id")
    session_type: str = _request.headers.get("X-Session-Type")

    async def start_pinger(interval: int = 25) -> None:
        try:
            while True:
                await asyncio.sleep(interval)
                try:
                    await ws.send(json.dumps({"type": "PING"}))
                except Exception:  # noqa: BLE001
                    break  # stop pinging if connection breaks
        except asyncio.CancelledError:
            pass

    # Start a background task to send pings every 25 seconds
    pinger_task = None
    try:
        pinger_task = asyncio.create_task(start_pinger())
        while True:
            payload_dict = await ws.recv()
            payload_dict = json.loads(payload_dict)
            payload_dict["session_id"] = session_id
            payload_dict["session_type"] = session_type

            if payload_dict.get("type") == "PAYLOAD_ATTACHMENT" and payload_dict.get("attachment_id"):
                attachment_id = payload_dict["attachment_id"]
                attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)
                if not attachment_data or getattr(attachment_data, "status", None) == "deleted":
                    raise ValueError(f"Attachment with ID {attachment_id} not found or already deleted.")
                s3_key = attachment_data.s3_key
                try:
                    object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)
                    s3_payload = json.loads(object_bytes.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    raise ValueError(f"Failed to decode JSON payload from S3: {e}")
                for field in ("session_id", "session_type", "auth_token"):
                    if field in payload_dict:
                        s3_payload[field] = payload_dict[field]
                payload_dict = s3_payload
                try:
                    await ChatFileUpload.delete_file_by_s3_key(s3_key=s3_key)
                except Exception:  # noqa: BLE001
                    AppLogger.log_error(f"Failed to delete S3 file {s3_key}")
                try:
                    await ChatAttachmentsRepository.update_attachment_status(attachment_id, "deleted")
                except Exception:  # noqa: BLE001
                    AppLogger.log_error(f"Failed to update status for attachment {attachment_id}")
            payload = QuerySolverInput(**payload_dict, user_team_id=auth_data.user_team_id)

            await CodeGenTasksCache.cleanup_session_data(payload.session_id)

            session_data_dict = {}
            if payload.query:
                session_data_dict["query"] = payload.query
                if payload.llm_model:
                    session_data_dict["llm_model"] = payload.llm_model.value
                await CodeGenTasksCache.set_session_data(payload.session_id, session_data_dict)

            async def solve_query() -> None:  # noqa: C901
                task_checker = CancellationChecker(payload.session_id)
                try:
                    await task_checker.start_monitoring()
                    start_data = {"type": "STREAM_START"}
                    if auth_data.session_refresh_token:
                        start_data["new_session_data"] = auth_data.session_refresh_token
                    await ws.send(json.dumps(start_data))

                    data = await QuerySolver().solve_query(
                        payload=payload, client_data=client_data, save_to_redis=True, task_checker=task_checker
                    )

                    last_block = None
                    async for data_block in data:
                        last_block = data_block
                        await ws.send(json.dumps(data_block.model_dump(mode="json")))

                    if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
                        await CodeGenTasksCache.cleanup_session_data(payload.session_id)
                        await ws.send(json.dumps({"type": "QUERY_COMPLETE"}))
                        await ws.send(json.dumps({"type": "STREAM_END_CLOSE_CONNECTION"}))
                    else:
                        await ws.send(json.dumps({"type": "STREAM_END"}))

                except LLMThrottledError as ex:
                    await ws.send(
                        json.dumps(
                            {
                                "type": "STREAM_ERROR",
                                "status": "LLM_THROTTLED",
                                "provider": getattr(ex, "provider", None),
                                "model": getattr(ex, "model", None),
                                "retry_after": ex.retry_after,
                                "message": "This chat is currently being throttled. You can wait, or switch to a different model.",
                                "detail": ex.detail,
                                "region": getattr(ex, "region", None),
                            }
                        )
                    )

                except InputTokenLimitExceededError as ex:
                    AppLogger.log_error(
                        f"Input token limit exceeded: model={ex.model_name}, tokens={ex.current_tokens}/{ex.max_tokens}"
                    )

                    # Get available models with higher token limits
                    better_models: List[Dict[str, Any]] = []

                    try:
                        code_gen_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
                        llm_models_config = ConfigManager.configs.get("LLM_MODELS", {})
                        current_model_limit = ex.max_tokens

                        for model in code_gen_models:
                            model_name = model.get("name")
                            if model_name and model_name != ex.model_name and model_name in llm_models_config:
                                model_config = llm_models_config[model_name]
                                model_token_limit = model_config.get("INPUT_TOKENS_LIMIT", 100000)

                                if model_token_limit > current_model_limit:
                                    enhanced_model = model.copy()
                                    enhanced_model["input_token_limit"] = model_token_limit
                                    better_models.append(enhanced_model)

                        # Sort by token limit (highest first)
                        better_models.sort(key=lambda m: m.get("input_token_limit", 0), reverse=True)

                    except Exception as model_error:  # noqa : BLE001
                        AppLogger.log_error(f"Error fetching better models: {model_error}")

                    error_data: Dict[str, Any] = {
                        "type": "STREAM_ERROR",
                        "status": "INPUT_TOKEN_LIMIT_EXCEEDED",
                        "model": ex.model_name,
                        "current_tokens": ex.current_tokens,
                        "max_tokens": ex.max_tokens,
                        "query": payload.query,
                        "message": f"Your message exceeds the context window supported by {get_model_display_name(ex.model_name)}. Try switching to a model with a higher context window to proceed.",
                        "detail": ex.detail,
                        "better_models": better_models,
                    }

                    await ws.send(json.dumps(error_data))

                except asyncio.CancelledError as ex:
                    await ws.send(json.dumps({"type": "STREAM_ERROR", "message": f"LLM processing error: {str(ex)}"}))
                except Exception as ex:  # noqa: BLE001
                    AppLogger.log_error(f"Error in solving query: {ex}")
                    await ws.send(json.dumps({"type": "STREAM_ERROR", "message": f"LLM processing error: {str(ex)}"}))
                finally:
                    await task_checker.stop_monitoring()

            _main_task = asyncio.create_task(solve_query())
    except Exception as error:
        if pinger_task:
            pinger_task.cancel()
        raise error
    finally:
        if pinger_task:
            pinger_task.cancel()


@code_gen_v2_bp.route("/start-message-thread-migration", methods=["POST"])
async def migrate_message_thread(_request: Request, **kwargs: Any) -> ResponseDict | response.JSONResponse:
    try:
        AppLogger.log_info("Starting message thread migration")

        # Simulate migration process
        _task = asyncio.create_task(MessageThreadMigrationManager.migrate_to_agent_chats())

        response_data = {"status": "success", "message": "Message thread migration started."}
        return send_response(response_data)

    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error during message thread migration: {e}")
        return send_response({"status": "error", "message": str(e)})
