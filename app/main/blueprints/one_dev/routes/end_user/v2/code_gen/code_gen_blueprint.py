import asyncio
import json
from typing import Any, Dict, List

from deputydev_core.exceptions.exceptions import InputTokenLimitExceededError
from deputydev_core.exceptions.llm_exceptions import (
    LLMThrottledError,
)
from deputydev_core.llm_handler.dataclasses.main import StreamingEventType
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from sanic import Blueprint, response
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.caches.code_gen_tasks_cache import (
    CodeGenTasksCache,
)
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
    QuerySolverInput,
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
)
from app.main.blueprints.one_dev.utils.session import (
    ensure_session_id,
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
