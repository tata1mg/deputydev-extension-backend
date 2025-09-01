from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.services.auth.supabase.session import SupabaseSession
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import HTTPRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.services.auth.auth import Auth
from app.main.blueprints.one_dev.services.auth.signup import SignUp
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

auth_v1_bp = Blueprint("auth_v1_bp", url_prefix="/auth")


@auth_v1_bp.route("/verify-auth-token", methods=["POST"])
@validate_client_version
async def verify_auth_token(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    headers = _request.headers
    payload = _request.custom_json() or {}
    response = await Auth.extract_and_verify_token(headers, payload)
    return send_response(response)


@auth_v1_bp.route("/get-session", methods=["GET"])
@validate_client_version
async def get_session(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    headers = _request.headers
    response = await SupabaseSession.get_session_by_supabase_session_id(headers)
    return send_response(response)


@auth_v1_bp.route("/sign-up", methods=["POST"])
@validate_client_version
async def sign_up(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    try:
        headers = _request.headers
        response = await SignUp.signup(headers)
        return send_response(response)
    except Exception as ex:  # noqa: BLE001
        raise HTTPRequestException(f"Failed to sign up: {str(ex)}")
