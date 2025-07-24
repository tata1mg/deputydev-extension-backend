import traceback
from typing import Any

from sanic import Blueprint, response
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException
from torpedo.types import ResponseDict

from app.backend_common.repository.extension_sessions.repository import (
    ExtensionSessionsRepository,
)
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.main.blueprints.one_dev.services.past_workflows.past_workflows import (
    PastWorkflows,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

history_v1_bp = Blueprint("history_v1_bp", url_prefix="/history")


@history_v1_bp.route("/chats", methods=["GET"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def get_chats(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    try:
        response = await PastWorkflows.get_past_chats(session_id=session_id, client_data=client_data)
    except Exception:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch past chats: {traceback.format_exc()}")
    return send_response(response, headers=kwargs.get("response_headers"))


@history_v1_bp.route("/sessions", methods=["GET"])
@validate_client_version
@authenticate
async def get_sessions(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    query_params = _request.args
    try:
        response = await PastWorkflows.get_past_sessions(
            user_team_id=auth_data.user_team_id,
            session_type=query_params["session_type"][0],
            sessions_list_type=query_params["sessions_list_type"][0],
            limit=int(int(query_params["limit"][0])) if query_params.get("limit") else None,
            offset=int(int(query_params["offset"][0])) if query_params.get("offset") else None,
            client_data=client_data,
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch past sessions: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))


@history_v1_bp.route("/pin-unpin-session", methods=["PUT"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def pin_unpin_session(
    _request: Request, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    query_params = _request.args
    try:
        await PastWorkflows.update_pinned_rank(
            session_id=session_id,
            user_team_id=auth_data.user_team_id,
            sessions_list_type=query_params["sessions_list_type"][0],
            pinned_rank=int(int(query_params["pinned_rank"][0])) if query_params.get("pinned_rank") else None,
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to pin/unpin session: {str(e)}")
    return send_response(headers=kwargs.get("response_headers"))


@history_v1_bp.route("/session-dragged", methods=["PUT"])
@validate_client_version
@authenticate
async def session_dragged(
    _request: Request, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    try:
        sessions_data = _request.custom_json()
        await ExtensionSessionsRepository.update_pinned_rank_by_session_ids(
            user_team_id=auth_data.user_team_id,
            sessions_data=sessions_data,
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to drag session: {str(e)}")
    return send_response(headers=kwargs.get("response_headers"))


@history_v1_bp.route("/delete-session", methods=["PUT"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def delete_session(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    try:
        await MessageSessionsRepository.soft_delete_message_session_by_id(
            session_id=session_id, user_team_id=auth_data.user_team_id
        )
        await ExtensionSessionsRepository.soft_delete_extension_session_by_id(
            session_id=session_id, user_team_id=auth_data.user_team_id
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to delete session: {str(e)}")
    return send_response(headers=kwargs.get("response_headers"))
