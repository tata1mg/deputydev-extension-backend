from sanic import Blueprint
from torpedo import Request, send_response

from app.main.blueprints.one_dev.services.config.config_fetcher import ConfigFetcher
from app.main.blueprints.one_dev.utils.pre_authenticate_handler import (
    validate_cli_version,
)

config = Blueprint("config", "/")


@config.route("/get-configs", methods=["GET"])
@validate_cli_version
async def get_configs(_request: Request, **kwargs):
    response = ConfigFetcher.fetch_configs_for_cli()
    return send_response(response)
