import json
from functools import wraps
from typing import Any, Dict, Tuple

import aiohttp
from deputydev_core.utils.context_value import ContextValue
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.service_clients.deputydev_auth.deputydev_auth import DeputyDevAuthClient
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from deputydev_core.utils.app_logger import AppLogger


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

    headers = {"Authorization": authorization_header}

    params = {
        "use_grace_period": str(use_grace_period).lower(),
        "enable_grace_period": str(enable_grace_period).lower(),
    }

    try:
        auth_response = await DeputyDevAuthClient().get_auth_data(headers=headers, params=params)
        auth_data: AuthData = AuthData(**auth_response["auth_data"])
        return auth_data, auth_response["response_headers"]
    except Exception as ex:
        AppLogger.log_error(str(ex))
        raise ex


def authenticate(func: Any) -> Any:
    """
    Wrapper to authenticate the user.
    """

    @wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        client_data: ClientData = kwargs.get("client_data")

        try:
            # Get the auth data
            auth_data, response_headers = await get_auth_data(request)
            kwargs["response_headers"] = response_headers
            ContextValue.set("response_headers", response_headers)

        except aiohttp.ClientResponseError as ex:
            upstream_status = getattr(ex, "status", None) or 500
            upstream_message = str(ex)

            # Websocket path: send error + close with auth-specific close code + return (no raise)
            if args and isinstance(args[0], WebsocketImplProtocol):
                ws = args[0]
                error_data : dict[str, Any] = {
                    "type": "STREAM_ERROR",
                    "message": "Unable to authenticate user",
                    "status": "NOT_VERIFIED",
                    "upstream_status": upstream_status,
                }
                await ws.send(json.dumps(error_data))
                await ws.close(code=4401, reason="NOT_VERIFIED")
                return

            # HTTP path: surface the upstream status (401/403/etc.)
            raise BadRequestException(
                upstream_message,
                status_code=upstream_status,
                sentry_raise=True,
            )

        except Exception as ex:  # noqa: BLE001
            if args and isinstance(args[0], WebsocketImplProtocol):
                ws = args[0]
                error_data = {
                    "type": "STREAM_ERROR",
                    "message": "Auth service unavailable",
                    "status": "NOT_VERIFIED",
                }
                await ws.send(json.dumps(error_data))
                await ws.close(code=1011, reason="AUTH_UNAVAILABLE")
                return

            raise BadRequestException(
                str(ex),
                status_code=503,
                sentry_raise=True,
            )

        kwargs = {
            **kwargs,
            "auth_data": auth_data,
            "client_data": client_data,
        }
        return await func(request, *args, **kwargs)

    return wrapper
