from functools import wraps
from typing import Any, Optional, Tuple

from deputydev_core.utils.constants.error_codes import APIErrorCodes
from torpedo import Request
from torpedo.exceptions import BadRequestException
from app.main.blueprints.one_dev.constants.constants import (
    MIN_SUPPORTED_CLI_VERSION,
    MIN_SUPPORTED_VSCODE_EXT_VERSION,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import (
    ClientData,
    Clients,
)
from app.main.blueprints.one_dev.utils.version import compare_version


def validate_version(client: Clients, client_version: str) -> Tuple[bool, Optional[str]]:
    is_valid = True
    min_version_supported = None
    if client == Clients.CLI:
        is_valid = compare_version(client_version, MIN_SUPPORTED_CLI_VERSION, ">=")
        if not is_valid:
            min_version_supported = MIN_SUPPORTED_CLI_VERSION
    else:
        is_valid = compare_version(client_version, MIN_SUPPORTED_VSCODE_EXT_VERSION, ">=")
        if not is_valid:
            min_version_supported = MIN_SUPPORTED_VSCODE_EXT_VERSION

    return is_valid, min_version_supported


def validate_client_version(func: Any):
    """
    Validate the client headers and raise a BadRequestException if the client version is not supported
    """

    @wraps(func)
    async def wrapper(_request: Request, **kwargs: Any) -> Any:
        client: Optional[str] = _request.headers.get("X-Client")
        if client is None:
            raise BadRequestException(
                error="Client header is missing", meta={"error_code": APIErrorCodes.CLIENT_HEADER_MISSING.value}
            )

        validated_client: Optional[Clients] = None
        try:
            validated_client = Clients(client)
        except ValueError:
            raise BadRequestException(error="Invalid client", meta={"error_code": APIErrorCodes.INVALID_CLIENT.value})

        client_version: Optional[str] = _request.headers.get("X-Client-Version")
        if client_version is None:
            raise BadRequestException(
                error="Client version is missing",
                meta={"error_code": APIErrorCodes.CLIENT_VERSION_HEADER_MISSING.value},
            )

        is_valid, upgrade_version = validate_version(client=validated_client, client_version=client_version)

        if not is_valid:
            raise BadRequestException(
                error=upgrade_version,
                meta={"error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value, "upgrade_version": upgrade_version},
            )

        return await func(
            _request, client_data=ClientData(client=validated_client, client_version=client_version), **kwargs
        )

    return wrapper
