from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

from app.main.blueprints.one_dev.services.repos.main import ReposHandler
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData

repos = Blueprint("repos", "/")

config = CONFIG.config


@repos.route("/get-registered-repo-details", methods=["GET"])
@authenticate
async def get_repos(_request: Request, auth_data: AuthData, **kwargs):
    payload = {key: var for key, var in _request.query_args}
    response = await ReposHandler.get_registered_repo_details(team_id=auth_data.team_id, **payload)
    return send_response(response)
