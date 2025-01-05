from sanic import Blueprint
from torpedo import Request, send_response

from app.main.blueprints.one_dev.services.auth.login_by_team import TeamLogin
from app.main.blueprints.one_dev.utils.pre_authenticate_handler import (
    validate_cli_version,
)

auth = Blueprint("auth", "/")


@auth.route("/verify-auth-token", methods=["POST"])
@validate_cli_version
async def verify_auth_token(_request: Request, **kwargs):
    payload = _request.custom_json()
    response = await TeamLogin.verify_auth_token(**payload)
    return send_response(response)
