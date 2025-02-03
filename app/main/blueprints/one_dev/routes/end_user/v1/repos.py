from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.one_dev.services.repos.main import ReposHandler
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.pre_authenticate_handler import (
    validate_cli_version,
)

repos = Blueprint("repos", "/")

config = CONFIG.config


@validate_cli_version
@repos.route("/get-registered-repo-details", methods=["GET"])
@authenticate
async def get_repos(_request: Request, auth_data: AuthData, **kwargs):
    payload = {key: var for key, var in _request.query_args}
    response = await ReposHandler.get_registered_repo_details(**payload)
    return send_response(response, headers=kwargs.get("headers"))
