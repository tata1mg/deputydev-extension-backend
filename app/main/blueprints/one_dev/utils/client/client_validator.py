import json
from functools import wraps
from typing import Any, Callable, Optional, Tuple

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.enums import Clients
from deputydev_core.utils.constants.error_codes import APIErrorCodes
from sanic.server.websockets.impl import WebsocketImplProtocol
from torpedo import Request
from torpedo.exceptions import BadRequestException

from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.constants.constants import (
    MIN_SUPPORTED_CLI_VERSION,
    MIN_SUPPORTED_VSCODE_EXT_VERSION,
    MIN_SUPPORTED_WEB_VERSION,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import StreamErrorData
from app.main.blueprints.one_dev.utils.version import compare_version


def validate_version(client: Clients, client_version: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates if the provided client version meets the minimum supported version.
    Returns whether the version is valid, the required version if not, and an optional download link.
    """
    is_valid = True
    min_version_supported = None
    download_link = None

    if client == Clients.CLI:
        is_valid = compare_version(client_version, MIN_SUPPORTED_CLI_VERSION, ">=")
        if not is_valid:
            min_version_supported = MIN_SUPPORTED_CLI_VERSION
    elif client == Clients.WEB:
        is_valid = compare_version(client_version, MIN_SUPPORTED_WEB_VERSION, ">=")
        if not is_valid:
            min_version_supported = MIN_SUPPORTED_WEB_VERSION
    elif client == Clients.PR_REVIEW:
        pass
    else:
        is_valid = compare_version(client_version, MIN_SUPPORTED_VSCODE_EXT_VERSION, ">=")
        if not is_valid:
            min_version_supported = MIN_SUPPORTED_VSCODE_EXT_VERSION
            download_link = ConfigManager.configs["CLIENT_DOWNLOAD_LINKS"].get(client.value)

    return is_valid, min_version_supported, download_link


def _extract_and_validate_client_data(_request: Request) -> ClientData:
    """
    Extracts and validates client-related headers from the request.
    Raises BadRequestException if headers are missing or invalid.
    """
    client = _request.headers.get("X-Client")
    if client is None:
        raise BadRequestException(
            error="Client header is missing",
            meta={"error_code": APIErrorCodes.CLIENT_HEADER_MISSING.value},
        )

    try:
        validated_client = Clients(client)
    except ValueError:
        raise BadRequestException(
            error="Invalid client",
            meta={"error_code": APIErrorCodes.INVALID_CLIENT.value},
        )

    client_version = _request.headers.get("X-Client-Version")
    if client_version is None:
        raise BadRequestException(
            error="Client version is missing",
            meta={"error_code": APIErrorCodes.CLIENT_VERSION_HEADER_MISSING.value},
        )

    return ClientData(client=validated_client, client_version=client_version.strip())


def validate_client_version(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that validates client version against minimum supported versions.
    Raises a BadRequestException if the client version is unsupported.
    """

    @wraps(func)
    async def wrapper(_request: Request, *args: Any, **kwargs: Any) -> Any:
        client_data = _extract_and_validate_client_data(_request)
        is_valid, upgrade_version, client_download_link = validate_version(
            client=client_data.client, client_version=client_data.client_version
        )

        if not is_valid:
            if args and isinstance(args[0], WebsocketImplProtocol):
                error_data = StreamErrorData(
                    type="STREAM_ERROR",
                    message={
                        "error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value,
                        "upgrade_version": upgrade_version,
                        **({"client_download_link": client_download_link} if client_download_link else {}),
                    },
                    status="INVALID_CLIENT_VERSION",
                )
                await args[0].send(json.dumps(error_data.model_dump(mode="json")))

            raise BadRequestException(
                error=upgrade_version,
                meta={
                    "error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value,
                    "upgrade_version": upgrade_version,
                    **({} if client_download_link is None else {"client_download_link": client_download_link}),
                },
            )
        kwargs = {
            **kwargs,
            "client_data": client_data,
        }
        return await func(_request, *args, **kwargs)

    return wrapper


def validate_client_headers_only(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that validates presence and correctness of client headers only.
    Does not check the version; only ensures headers are valid.
    """

    @wraps(func)
    async def wrapper(_request: Request, **kwargs: Any) -> Any:
        client_data = _extract_and_validate_client_data(_request)
        return await func(_request, client_data=client_data, **kwargs)

    return wrapper
