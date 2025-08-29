from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException
from torpedo.response import ResponseDict

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.models.dto.url import UrlDto
from app.main.blueprints.one_dev.services.urls.url_service import UrlService
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.session import ensure_session_id

urls_v1_bp = Blueprint("urls_v1_bp", url_prefix="/urls")


@urls_v1_bp.route("/saved_url/list", methods=["GET"])
@validate_client_version
@authenticate
async def list_saved_urls(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    try:
        response = await UrlService.get_saved_urls(
            user_team_id=auth_data.user_team_id,
            limit=int(query_params.get("limit", 5)),
            offset=int(query_params.get("offset", 0)),
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch saved URLs: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))


@urls_v1_bp.route("/summarize_url", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def summarize_urls(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = _request.json
    try:
        response = await UrlService.summarize_urls_long_content(session_id=session_id, content=payload.get("content"))
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch saved URLs: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))


@urls_v1_bp.route("/save_url", methods=["POST"])
@validate_client_version
@authenticate
async def save_url(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = _request.json
    try:
        payload["user_team_id"] = auth_data.user_team_id
        payload = UrlDto(**payload)
        response = await UrlService.save_url(payload)
    except Exception as e:  # noqa: BLE001
        raise e
    return send_response(response, headers=kwargs.get("response_headers"))


@urls_v1_bp.route("/update_url", methods=["PUT"])
@validate_client_version
@authenticate
async def update_url(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = _request.json
    try:
        payload["user_team_id"] = auth_data.user_team_id
        payload = UrlDto(**payload)
        response = await UrlService.update_url(payload)
    except Exception as e:  # noqa: BLE001
        raise e
    return send_response(response, headers=kwargs.get("response_headers"))


@urls_v1_bp.route("/delete_url", methods=["GET"])
@validate_client_version
@authenticate
async def delete_url(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    url_id = int(query_params.get("url_id"))
    try:
        response = await UrlService.delete_url(url_id)
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch saved URLs: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))
