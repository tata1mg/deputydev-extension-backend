from sanic import Blueprint
from torpedo import Request, send_response

from app.main.blueprints.one_dev.services.past_workflows.past_workflows import PastWorkflows

history = Blueprint("history", "/")

@history.route("/chats", methods=["GET"])
async def get_chats(_request: Request, **kwargs):
    response = await PastWorkflows.get_past_chats()
    return send_response(response)

@history.route("/sessions", methods=["GET"])
async def get_sessions(_request: Request, **kwargs):
    user_team_id = 1
    response = await PastWorkflows.get_past_sessions(user_team_id)
    return send_response(response)