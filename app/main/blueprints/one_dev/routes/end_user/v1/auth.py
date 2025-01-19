from sanic import Blueprint
from torpedo import Request, send_response

from app.backend_common.repository.user_teams.user_team_service import UserTeamService
from app.backend_common.repository.users.user_service import UserService
from app.backend_common.services.supabase.session import SupabaseSession
from app.main.blueprints.one_dev.services.auth.login import Login
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


@auth.route("register-user", methods=["POST"])
@validate_cli_version
async def register_user(_request: Request, **kwargs):
    headers = _request.headers
    response = await UserService.find_or_create(
        headers.get("X-User-Name"),
        headers.get("X-User-Email"),
        headers.get("X-Organization"),
    )
    return send_response(response)


@auth.route("register-user-team", methods=["POST"])
@validate_cli_version
async def register_user_team(_request: Request, **kwargs):
    headers = _request.headers
    response = await UserTeamService.find_or_create(
        headers.get("X-Team-Id"),
        headers.get("X-User-Id"),
        headers.get("X-Role"),
        headers.get("X-Is-Owner"),
        headers.get("X-Is-Billable"),
    )
    return send_response(response)
