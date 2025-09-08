from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.services.repos.main import ReposHandler
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

repos_v1_bp = Blueprint("repos_v1_bp", url_prefix="/repos")


@repos_v1_bp.route("/get-registered-repo-details", methods=["GET"])
@validate_client_version
@authenticate
async def get_repos(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = {key: var for key, var in _request.query_args}
    response = await ReposHandler.get_registered_repo_details(**payload)
    return send_response(response, headers=kwargs.get("response_headers"))
