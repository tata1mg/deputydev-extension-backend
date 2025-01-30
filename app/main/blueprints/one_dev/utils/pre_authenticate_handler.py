from functools import wraps

from torpedo import Request
from torpedo.exceptions import BadRequestException

from app.common.constants.error_codes import APIErrorCodes
from app.main.blueprints.one_dev.constants.constants import DEPRECATED_CLI_VERSIONS


def validate_version(cli_version):
    is_valid, message = True, ""
    if cli_version in DEPRECATED_CLI_VERSIONS:
        upgradeable_version_suggest = DEPRECATED_CLI_VERSIONS[cli_version] or "latest"
        message = f"Unsupported version please upgrade to {upgradeable_version_suggest}"
        is_valid = False
    return is_valid, message


def validate_cli_version(func):
    """
    Wrapper to authenticate the user using the JWT token.
    """

    @wraps(func)
    async def wrapper(_request: Request, **kwargs):
        cli_version = _request.headers.get("x-cli-app-version")
        is_valid, message = validate_version(cli_version)
        if not is_valid:
            raise BadRequestException(error=message, meta={"error_code": APIErrorCodes.INVALID_CLIENT_VERSION.value})
        return await func(_request, **kwargs)

    return wrapper
