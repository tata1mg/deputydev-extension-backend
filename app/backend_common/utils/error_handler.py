from __future__ import annotations

import typing as t

from deputydev_core.utils.context_value import ContextValue
from sanic import response
from sanic.handlers import ErrorHandler
from sanic.log import error_logger
from typing_extensions import override

from app.backend_common.utils.sanic_wrapper.constants.errors import (
    HANDLED_ERR,
    INTERSERVICE_ERR,
    SOMETHING_WENT_WRONG,
    UNHANDLED_ERR,
)
from app.backend_common.utils.sanic_wrapper.constants.headers import USER_AGENT, X_SERVICE_NAME
from app.backend_common.utils.sanic_wrapper.constants.http import STATUS_CODE_4XX, STATUS_CODE_MAPPING, HTTPStatusCodes
from app.backend_common.utils.sanic_wrapper.ctx import app_ctx
from app.backend_common.utils.sanic_wrapper.request import TorpedoRequest
from app.backend_common.utils.sanic_wrapper.types import ErrorResponseDict
from app.backend_common.utils.sanic_wrapper.utils import capture_exception, name

############################
# import tortoise excpetions
############################


# tortoise-orm is removed from app.backend_common.utils.sanic_wrapper since v4
# so we check if tortoise is present in the env
# and handle the exceptions accordingly.
TORTOISE: bool = False

try:
    import tortoise  # noqa
except ImportError:
    TORTOISE = False
else:
    TORTOISE = True

    from tortoise.exceptions import (
        BaseORMException,
        DoesNotExist,
        FieldError,
        IncompleteInstanceError,
        IntegrityError,
        MultipleObjectsReturned,
        NoValuesFetched,
        OperationalError,
        ParamsError,
        TransactionManagementError,
        ValidationError,
    )

    TORTOISE_400_EXC = (
        FieldError,
        ParamsError,
        TransactionManagementError,
        OperationalError,
        IntegrityError,
        NoValuesFetched,
        MultipleObjectsReturned,
        DoesNotExist,
        IncompleteInstanceError,
        ValidationError,
    )

##########################
# import sanic excpetions
##########################

from sanic.exceptions import (  # noqa: E402
    Forbidden,
    MethodNotSupported,
    NotFound,
    PayloadTooLarge,
    RequestTimeout,
    SanicException,
    Unauthorized,
)

HANDLED_SANIC_EXC = (
    MethodNotSupported,
    NotFound,
    Unauthorized,
    Forbidden,
    RequestTimeout,
    PayloadTooLarge,
)

###########################
# import torpedo excpetions
###########################

from app.backend_common.utils.sanic_wrapper.exceptions import (  # noqa: E402
    BadRequestException,
    BaseTorpedoException,
    ForbiddenException,
    InterServiceRequestException,
    JsonDecodeException,
    NotFoundException,
)

HANDLED_TORPEDO_EXC = (
    BadRequestException,
    JsonDecodeException,
    NotFoundException,
    ForbiddenException,
)


def exception_response(
    exception: Exception,
    /,
    error: str | dict | None = None,
    status_code: int | None = None,
    *,
    meta: t.Any = None,
    response_headers: t.Optional[dict],
) -> response.JSONResponse:
    error = error or str(exception)

    status_code = status_code or getattr(exception, "status_code", None)

    if not status_code:
        status_code = int(HTTPStatusCodes.INTERNAL_SERVER_ERROR)

    if getattr(exception, "custom_http_codes_mapping_enabled", True):
        status_code = STATUS_CODE_MAPPING.get(status_code, status_code)

    if not isinstance(error, dict):
        error_list = []
        error_content = None

        if error_id := getattr(exception, "error_id", None):
            # get detailed error content using the error_id
            # this looks up `error_content` dictionary
            # if attached to app context on service startup

            # NOTE: this might be useful but it is a legacy artefact
            # and better API could be possible.

            error_content = app_ctx().error_content.get(error_id)

        if error_content:
            error_list.append(error_content)
        else:
            # NOTE: This nested error with prima facie incorrect semantics
            # is a legacy artefact. It cannot go right now as it would break
            # uniformity in error messages across platform.

            error_list.append({"message": error})

        error = {
            "message": error,
            "errors": error_list,
        }

    retval: ErrorResponseDict = {
        "error": error,
        "is_success": False,
        "status_code": status_code,
    }

    if error_code := getattr(exception, "error_code", None):
        retval["error_code"] = error_code

    if meta := meta or getattr(exception, "meta", None):
        retval["meta"] = meta

    return response.json(body=retval, status=status_code, headers=response_headers)


class DDErrorHandler(ErrorHandler):
    @override
    def default(self, req: TorpedoRequest, exc: Exception) -> response.JSONResponse:  # noqa:PLR0911
        """Handle exceptions and send error response.

        Default handler for exceptions. All uncaught exceptions, if not handled
        by any service level exception handler, are handled here.

        Args:
            req (TorpedoRequest): request object
            exc (Exception): uncaught exception

        Returns:
            response.JSONResponse: error response.
        """
        response_headers = ContextValue.get("response_headers") or {}
        try:
            req_info = self.__get_req_info(req)
        except Exception:  # noqa: BLE001
            req_info = {}

        # ---------------------------------------------------------------------------- #
        #                            Tortoise ORM exceptions                           #
        # ---------------------------------------------------------------------------- #

        if TORTOISE:
            if isinstance(exc, BaseORMException):  # noqa
                return self._handle_tortoise_exceptions(req, exc)

        # ---------------------------------------------------------------------------- #
        #                    BaseTorpedoException derived exceptions                   #
        # ---------------------------------------------------------------------------- #

        if isinstance(exc, HANDLED_TORPEDO_EXC):
            error_logger.info(HANDLED_ERR.format(name(exc), req.endpoint))
            return exception_response(exc, error=exc.error, response_headers=response_headers)

        if isinstance(exc, InterServiceRequestException):
            if exc.status_code in STATUS_CODE_4XX:
                error_logger.info(INTERSERVICE_ERR.format(name(exc), req.endpoint))
                return exception_response(exc, response_headers=response_headers)

            error_logger.error(f"[{name(exc)}] {str(exc)}", extra=req_info)
            error_logger.exception(INTERSERVICE_ERR.format(name(exc), req.endpoint))
            capture_exception()
            return exception_response(exc, response_headers=response_headers)

        ...

        if isinstance(exc, BaseTorpedoException):
            error_logger.error(f"[{name(exc)}] {str(exc)}", extra=req_info)
            error_logger.exception(UNHANDLED_ERR.format(name(exc), req.endpoint))
            capture_exception(handled=False)
            return exception_response(exc, response_headers=response_headers)

        # ---------------------------------------------------------------------------- #
        #                       SanicException derived exceptions                      #
        # ---------------------------------------------------------------------------- #

        if isinstance(exc, HANDLED_SANIC_EXC):
            error_logger.error(HANDLED_ERR.format(name(exc), req.endpoint))
            capture_exception()
            return exception_response(exc, response_headers=response_headers)

        ...

        if isinstance(exc, SanicException):
            error_logger.error(f"[{name(exc)}] {str(exc)}")
            error_logger.exception(UNHANDLED_ERR.format(name(exc), req.endpoint))
            capture_exception(handled=False)
            return exception_response(exc, response_headers=response_headers)

        # ---------------------------------------------------------------------------- #
        #                             Unhandled exceptions                             #
        # ---------------------------------------------------------------------------- #

        error_logger.error(f"[{name(exc)}] {str(exc)}", extra=req_info)
        error_logger.exception(UNHANDLED_ERR.format(name(exc), req.endpoint))
        capture_exception(handled=False)

        return exception_response(
            exc,
            error=SOMETHING_WENT_WRONG,
            status_code=HTTPStatusCodes.INTERNAL_SERVER_ERROR.value,
            response_headers=response_headers,
        )

    def __get_req_info(self, request: TorpedoRequest):
        req_info = {
            "method": request.method,
            "uri": request.path,
            "content_type": request.content_type,
            "params": request.args,
            "headers": request.headers,
            # client info
            "client.ip": request.ip,
            "client.service_name": request.headers.get(X_SERVICE_NAME),
            "client.user_agent": request.headers.get(USER_AGENT),
        }

        if request.method != "GET":
            try:
                req_info["body"] = request.json
            except Exception:
                req_info["body"] = "[FAILED TO PARSE]"

        return req_info

    # ---------------------------------------------------------------------------- #

    def _handle_tortoise_exceptions(self, req: TorpedoRequest, exc: BaseORMException):
        """Default handler for tortoise exceptions."""

        if isinstance(exc, TORTOISE_400_EXC):
            error_logger.info(HANDLED_ERR.format(name(exc), req.endpoint))
            return exception_response(
                exc,
                status_code=HTTPStatusCodes.BAD_REQUEST.value,
            )

        error_logger.info(HANDLED_ERR.format(name(exc), req.endpoint))
        return exception_response(
            exc,
            status_code=HTTPStatusCodes.INTERNAL_SERVER_ERROR.value,
        )
