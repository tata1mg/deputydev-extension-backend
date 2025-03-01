from sanic import Blueprint
from torpedo import Request, send_response

from app.backend_common.repository.message_sessions.repository import MessageSessionsRepository
from app.main.blueprints.one_dev.services.past_workflows.past_workflows import PastWorkflows
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData

history = Blueprint("history", "/")

@history.route("/chats", methods=["GET"])
@authenticate
async def get_chats(_request: Request, auth_data: AuthData, **kwargs):
  headers = _request.headers
  response = await PastWorkflows.get_past_chats(session_id=headers.get("X-Session-ID"))
  return send_response(response)

@history.route("/sessions", methods=["GET"])
@authenticate
async def get_sessions(_request: Request, auth_data: AuthData, **kwargs):
  headers = _request.headers
  response = await PastWorkflows.get_past_sessions(user_team_id=auth_data.user_team_id, headers=headers)
  return send_response(response)

@history.route("/delete_session", methods=["PUT"])
@authenticate
async def delete_session(_request: Request, auth_data: AuthData, **kwargs):
  headers = _request.headers
  response = await MessageSessionsRepository.soft_delete_message_session_by_id(session_id=headers.get("X-Session-ID"), user_team_id=auth_data.user_team_id)
  return send_response(response)