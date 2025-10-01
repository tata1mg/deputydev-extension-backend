import asyncio
import json
from typing import Any, Dict, List

from deputydev_core.utils.config_manager import ConfigManager
from sanic import Blueprint, response
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.caches.code_gen_tasks_cache import CodeGenTasksCache
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
    QuerySolverInput,
    QuerySolverResumeInput,
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
async def solve_user_query_ws(
    _request: Request, ws: WebsocketImplProtocol, client_data: ClientData, auth_data: AuthData, session_id: int
) -> None:
    # TODO: Remove after MessageSession deprecation
    session_type: str = _request.headers.get("X-Session-Type")

    # Initialize query solver
    query_solver = QuerySolver()

    # Start a background task to send pings every 25 seconds to keep the websocket alive
    pinger_task = None
    try:
        pinger_task = asyncio.create_task(query_solver.start_pinger(ws))

        while True:
            payload_dict = await ws.recv()
            payload_dict = json.loads(payload_dict)
            payload_dict["session_id"] = session_id
            payload_dict["session_type"] = session_type

            # Case 1: S3 payload (has attachment_id)
            if query_solver._is_s3_payload(payload_dict):
                payload_dict = await query_solver.process_s3_payload(payload_dict)

            # Case 2: Resume payload - check if it has resume_query_id
            if payload_dict.get("resume_query_id"):
                payload = QuerySolverResumeInput(**payload_dict, user_team_id=auth_data.user_team_id)
            else:
                # Case 3: Normal payload
                payload = QuerySolverInput(**payload_dict, user_team_id=auth_data.user_team_id)
                # Handle session data caching (skip for resume payloads)
                await query_solver.handle_session_data_caching(payload)

            # Execute query processing
            _main_task = asyncio.create_task(query_solver.execute_query_processing(payload, client_data, auth_data, ws))

    except Exception as error:
        if pinger_task:
            pinger_task.cancel()
        raise error
    finally:
        if pinger_task:
            pinger_task.cancel()
