from typing import Any, Dict, Optional

from deputydev_core.utils.constants.enums import Clients
from deputydev_core.utils.constants.error_codes import APIErrorCodes
from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.services.config.config_fetcher import ConfigFetcher
from app.main.blueprints.one_dev.services.config.dataclasses.main import (
    ConfigParams,
    ConfigType,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

config_v1_bp = Blueprint("config_v1_bp", url_prefix="/configs")


@config_v1_bp.route("/get-essential-configs", methods=["GET"])
async def get_essential_configs(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    client_version: str = _request.headers.get("X-Client-Version")

    try:
        client_str: str = _request.headers.get("X-Client")
        client = Clients(client_str)
    except ValueError:
        raise BadRequestException(
            error="Invalid client", meta={"error_code": APIErrorCodes.INVALID_CLIENT.value}, sentry_raise=False
        )

    client_data = ClientData(client=client, client_version=client_version)
    params: Optional[ConfigParams] = None
    try:
        query_params: Dict[str, Any] = _request.request_params()
        params = ConfigParams(**query_params)
    except Exception:  # noqa: BLE001
        raise BadRequestException(error="Invalid query params", sentry_raise=False)
    response = await ConfigFetcher.fetch_configs(
        params=params, config_type=ConfigType.ESSENTIAL, client_data=client_data
    )
    return send_response(response)


@config_v1_bp.route("/get-configs", methods=["GET"])
@validate_client_version
@authenticate
async def get_configs(_request: Request, client_data: ClientData, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.request_params()
    params = ConfigParams(**query_params)
    response = await ConfigFetcher.fetch_configs(params=params, config_type=ConfigType.MAIN, client_data=client_data)
    return send_response(response, headers=kwargs.get("response_headers"))
