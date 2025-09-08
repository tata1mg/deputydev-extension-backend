from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.services.auth.auth_factory import AuthFactory
from app.backend_common.services.auth.signup import SignUp
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import HTTPRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

auth_v1_bp = Blueprint("auth_v1_bp", url_prefix="/auth")


@auth_v1_bp.route("/verify-auth-token", methods=["POST"])
@validate_client_version
async def verify_auth_token(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    auth_provider = AuthFactory.get_auth_provider()
    response = await auth_provider.extract_and_verify_token(_request)
    return send_response(response.model_dump(mode="json"))


@auth_v1_bp.route("/get-session", methods=["GET"])
@validate_client_version
async def get_session(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    headers = _request.headers
    auth_provider = AuthFactory.get_auth_provider()
    response = await auth_provider.get_auth_session(headers)
    return send_response(response.model_dump(mode="json"))


@auth_v1_bp.route("/sign-up", methods=["POST"])
@validate_client_version
async def sign_up(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    try:
        headers = _request.headers
        response = await SignUp.signup(headers)
        return send_response(response)
    except Exception as ex:  # noqa: BLE001
        raise HTTPRequestException(f"Failed to sign up: {str(ex)}")
