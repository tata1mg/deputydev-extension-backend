from typing import Any

from sanic import Blueprint
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException
from app.main.blueprints.one_dev.utils.session import ensure_session_id
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.services.web_search.web_search_service import WebSearchService
from app.main.blueprints.one_dev.models.dto.url import UrlDto

websearch_v1_bp = Blueprint("websearch_bp", url_prefix="/websearch")


@websearch_v1_bp.route("/", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def websearch(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any):
    payload = _request.json
    try:
        response = await WebSearchService.web_search(session_id=session_id, query=payload.get("descriptive_query"))
    except Exception as e:
        raise BadRequestException(f"Failed to search from web: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))
