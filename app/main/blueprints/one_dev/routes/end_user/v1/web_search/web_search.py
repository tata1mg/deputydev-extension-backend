from typing import Any

from sanic import Blueprint
from sanic.exceptions import ServerError
from sanic.response import JSONResponse

from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.services.web_search.web_search_service import (
    WebSearchService,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

websearch_v1_bp = Blueprint("websearch_bp", url_prefix="/websearch")


@websearch_v1_bp.route("/", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def websearch(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = _request.json
    if not payload.get("descriptive_query"):
        raise BadRequestException("Missing descriptive query")
    try:
        response = await WebSearchService.web_search(session_id=session_id, query=payload.get("descriptive_query"))
        return send_response(response, headers=kwargs.get("response_headers"))
    except Exception as e:  # noqa: BLE001
        raise ServerError(f"Failed to search from web: {str(e)}")
