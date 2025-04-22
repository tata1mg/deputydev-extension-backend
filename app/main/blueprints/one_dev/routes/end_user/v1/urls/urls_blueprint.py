from typing import Any

from sanic import Blueprint
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException
from app.main.blueprints.one_dev.utils.session import ensure_session_id
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.services.urls.url_service import UrlService

urls_v1_bp = Blueprint("urls_v1_bp", url_prefix="/urls")


@urls_v1_bp.route("/saved_url/list", methods=["GET"])
@validate_client_version
@authenticate
async def list_saved_urls(_request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any):
    query_params = _request.args
    try:
        response = await UrlService.get_saved_urls(
            user_team_id=auth_data.user_team_id,
            limit=int(query_params.get("limit", [5])[0]),
            offset=int(query_params.get("offset", [0])[0]),
            client_data=client_data,
        )
    except Exception as e:
        raise BadRequestException(f"Failed to fetch saved URLs: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))


@urls_v1_bp.route("/summarize_url", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def summarize_urls(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.json
    try:
        response = await UrlService.summarize_urls_long_content(session_id=session_id, content=payload.get("content"))
    except Exception as e:
        raise BadRequestException(f"Failed to fetch saved URLs: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))
