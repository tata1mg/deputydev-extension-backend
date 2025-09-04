import json
from functools import wraps
from typing import Any, Dict, Tuple

import aiohttp
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.context_value import ContextValue
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException


async def get_auth_data(request: Request) -> Tuple[AuthData, Dict[str, Any]]:  # noqa: C901
    """
    Get the auth data by calling the auth service API using aiohttp
    """
    use_grace_period: bool = False
    enable_grace_period: bool = False
    payload: Dict[str, Any] = {}

    authorization_header: str = request.headers.get("Authorization")
    if not authorization_header:
        raise BadRequestException("Authorization header is missing")

    try:
        payload = request.custom_json() if request.method == "POST" else request.request_params()
        use_grace_period = payload.get("use_grace_period") or False
        enable_grace_period = payload.get("enable_grace_period") or False
    except Exception:  # noqa: BLE001
        pass

    dd_auth_service_host = ConfigManager.configs["DD_AUTH_SERVICE_HOST"]
    dd_get_auth_endpoint = ConfigManager.config["DD_AUTH_SERVICE_GET_AUTH_DATA_ENDPOINT"]
    auth_service_url = f"{dd_auth_service_host}{dd_get_auth_endpoint}"

    headers = {"Authorization": authorization_header}

    params = {
        "use_grace_period": str(use_grace_period).lower(),
        "enable_grace_period": str(enable_grace_period).lower(),
    }

    async with aiohttp.ClientSession() as session:
        response = await session.get(auth_service_url, headers=headers, params=params)
        response_data = await response.json()
        if response_data:
            auth_data = AuthData(**response_data.get("auth_data"))
            response_headers = response_data.get("response_headers", {})
            return auth_data, response_headers
        else:
            raise BadRequestException("Auth Data is missing")


def authenticate(func: Any) -> Any:
    """
    Wrapper to authenticate the user.
    """

    @wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        try:
            # Get the auth data
            client_data: ClientData = kwargs.get("client_data")
            auth_data, response_headers = await get_auth_data(request)
            kwargs["response_headers"] = response_headers
            ContextValue.set("response_headers", response_headers)
        except Exception as ex:  # noqa: BLE001
            if args and isinstance(args[0], WebsocketImplProtocol):
                error_data = {
                    "type": "STREAM_ERROR",
                    "message": "Unable to authenticate user",
                    "status": "NOT_VERIFIED",
                }
                await args[0].send(json.dumps(error_data))
            raise BadRequestException(str(ex), sentry_raise=False)
        kwargs = {
            **kwargs,
            "auth_data": auth_data,
            "client_data": client_data,
        }
        return await func(request, *args, **kwargs)

    return wrapper
