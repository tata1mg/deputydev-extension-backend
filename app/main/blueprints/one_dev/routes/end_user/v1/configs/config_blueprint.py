from deputydev_core.utils.constants.enums import ConfigConsumer
from sanic import Blueprint
from torpedo import Request, send_response

from app.main.blueprints.one_dev.services.config.config_fetcher import ConfigFetcher
from app.main.blueprints.one_dev.services.config.dataclasses.main import ConfigType
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData

config_v1_bp = Blueprint("config_v1_bp", url_prefix="/configs")


@config_v1_bp.route("/get-essential-configs", methods=["GET"])
@validate_client_version
async def get_essential_configs(_request: Request, client_data: ClientData, **kwargs):
    query_params = _request.request_params()
    value = ConfigConsumer[query_params.get("consumer")]
    response = ConfigFetcher.fetch_configs(consumer=value, config_type=ConfigType.ESSENTIAL)
    return send_response(response)


@config_v1_bp.route("/get-configs", methods=["GET"])
@validate_client_version
@authenticate
async def get_configs(_request: Request, client_data: ClientData, **kwargs):
    query_params = _request.request_params()
    value = ConfigConsumer[query_params.get("consumer")]
    response = ConfigFetcher.fetch_configs(consumer=value, config_type=ConfigType.MAIN)
    return send_response(response, headers=kwargs.get("response_headers"))
