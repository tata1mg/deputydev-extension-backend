import traceback
from typing import Any

from sanic import Blueprint, response

from app.backend_common.repository.extension_sessions.repository import (
    ExtensionSessionsRepository,
)
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.services.history.code_gen_agent_chats.code_gen_agent_chats_manager import (
    PastCodeGenAgentChatsManager,
)
from app.main.blueprints.one_dev.services.history.sessions.dataclasses.sessions import (
    PastSessionsInput,
    PinnedRankUpdateInput,
)
from app.main.blueprints.one_dev.services.history.sessions.sessions_manager import PastSessionsManager
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
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
        response = await PastCodeGenAgentChatsManager.get_past_chats(session_id=session_id)
    except Exception:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch past chats: {traceback.format_exc()}")
    return send_response(
        [chat_element.model_dump(mode="json") for chat_element in response], headers=kwargs.get("response_headers")
    )


@history_v1_bp.route("/sessions", methods=["GET"])
@validate_client_version
@authenticate
async def get_sessions(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    query_params = _request.args
    try:
        formatted_sessions, has_more = await PastSessionsManager.get_past_sessions(
            PastSessionsInput(
                user_team_id=auth_data.user_team_id,
                session_type=query_params["session_type"][0],
                sessions_list_type=query_params["sessions_list_type"][0],
                limit=int(int(query_params["limit"][0])) if query_params.get("limit") else None,
                offset=int(int(query_params["offset"][0])) if query_params.get("offset") else None,
            )
        )
        return send_response(
            {"sessions": [session.model_dump(mode="json") for session in formatted_sessions], "has_more": has_more},
            headers=kwargs.get("response_headers"),
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch past sessions: {str(e)}")


@history_v1_bp.route("/pin-unpin-session", methods=["PUT"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def pin_unpin_session(
    _request: Request, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | response.JSONResponse:
    query_params = _request.args
    try:
        await PastSessionsManager.update_pinned_rank(
            PinnedRankUpdateInput(
                session_id=session_id,
                user_team_id=auth_data.user_team_id,
                sessions_list_type=query_params["sessions_list_type"][0],
                pinned_rank=int(int(query_params["pinned_rank"][0])) if query_params.get("pinned_rank") else None,
            )
        )
        return send_response(headers=kwargs.get("response_headers"))
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to pin/unpin session: {str(e)}")


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
