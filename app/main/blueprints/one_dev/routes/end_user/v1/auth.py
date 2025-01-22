from sanic import Blueprint
from torpedo import Request, send_response

from app.backend_common.services.supabase.session import SupabaseSession
from app.main.blueprints.one_dev.services.auth.login import Login
from app.main.blueprints.one_dev.services.auth.signup import SignUp
from app.main.blueprints.one_dev.utils.pre_authenticate_handler import (
    validate_cli_version,
)

auth = Blueprint("auth", "/")


@auth.route("/verify-auth-token", methods=["POST"])
@validate_cli_version
async def verify_auth_token(_request: Request, **kwargs):
    headers = _request.headers
    response = await Login.verify_auth_token(headers)
    return send_response(response)


@auth.route("/get-session", methods=["GET"])
@validate_cli_version
async def get_session(_request: Request, **kwargs):
    headers = _request.headers
    response = await SupabaseSession.get_session_by_device_code(headers)
    return send_response(response)


@auth.route("sign-up", methods=["POST"])
@validate_cli_version
async def sign_up(_request: Request, **kwargs):
    headers = _request.headers
    response = await SignUp.signup(headers)
    return send_response(response)
