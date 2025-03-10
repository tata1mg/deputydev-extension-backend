from typing import Any, Dict
from sanic import Blueprint
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException

from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.chat_history_handler import ChatHistoryHandler
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import PreviousChatPayload
from app.main.blueprints.one_dev.services.past_workflows.past_workflows import (
    PastWorkflows,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

history_v1_bp = Blueprint("history_v1_bp", url_prefix="/history")


@history_v1_bp.route("/chats", methods=["GET"])
@validate_client_version
@authenticate
async def get_chats(_request: Request, auth_data: AuthData, **kwargs):
    headers = _request.headers
    try:
        response = await PastWorkflows.get_past_chats(session_id=headers.get("X-Session-ID"))
    except Exception as e:
        raise BadRequestException(f"Failed to fetch past chats: {str(e)}")
    return send_response(response)


@history_v1_bp.route("/sessions", methods=["GET"])
@validate_client_version
@authenticate
async def get_sessions(_request: Request, auth_data: AuthData, **kwargs):
    headers = _request.headers
    try:
        response = await PastWorkflows.get_past_sessions(user_team_id=auth_data.user_team_id, headers=headers)
    except Exception as e:
        raise BadRequestException(f"Failed to fetch past sessions: {str(e)}")
    return send_response(response)


@history_v1_bp.route("/delete-session", methods=["PUT"])
@validate_client_version
@authenticate
async def delete_session(_request: Request, auth_data: AuthData, **kwargs):
    headers = _request.headers
    try:
        response = await MessageSessionsRepository.soft_delete_message_session_by_id(
            session_id=headers.get("X-Session-ID"), user_team_id=auth_data.user_team_id
        )
    except Exception as e:
        raise BadRequestException(f"Failed to delete session: {str(e)}")
    return send_response(response)


@history_v1_bp.route("/relevant-chat-history", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(session_type="CODE_GENERATION_V1")
async def fetch_relevant_chat_history(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload: Dict[str, Any] = _request.custom_json()
    response = await ChatHistoryHandler(
        PreviousChatPayload(query=payload["query"], session_id=session_id)
    ).get_relevant_previous_chats()
    return send_response(response, headers=kwargs.get("response_headers"))
