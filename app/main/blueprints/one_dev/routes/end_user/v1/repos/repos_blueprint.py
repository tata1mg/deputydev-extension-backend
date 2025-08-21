from typing import Any

from sanic import Blueprint
from app.backend_common.utils.sanic_wrapper import Request, send_response

from app.main.blueprints.one_dev.services.repos.main import ReposHandler
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData

repos_v1_bp = Blueprint("repos_v1_bp", url_prefix="/repos")


@repos_v1_bp.route("/get-registered-repo-details", methods=["GET"])
@validate_client_version
@authenticate
async def get_repos(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any):
    payload = {key: var for key, var in _request.query_args}
    response = await ReposHandler.get_registered_repo_details(**payload)
    return send_response(response, headers=kwargs.get("response_headers"))
