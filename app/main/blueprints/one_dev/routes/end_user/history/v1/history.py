from sanic import Blueprint
from torpedo import Request, send_response

history = Blueprint("history", "/")

@history.route("/chats", methods=["GET"])
async def get_chats(_request: Request, **kwargs):
    return send_response({"message": "chats"})

@history.route("/sessions", methods=["GET"])
async def get_sessions(_request: Request, **kwargs):
    return send_response({"message": "sessions"})