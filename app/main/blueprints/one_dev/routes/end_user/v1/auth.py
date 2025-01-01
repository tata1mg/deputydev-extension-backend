from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.one_dev.services.auth.login_by_team import TemaLogin

auth = Blueprint("auth", "/")

config = CONFIG.config


@auth.route("/verify-auth-token", methods=["POST"])
async def verify_auth_token(_request: Request, **kwargs):
    payload = _request.custom_json()
    response = await TemaLogin.verify_auth_token(**payload)
    return send_response(response)
