from __future__ import annotations

import functools
import typing as t

from sanic import response

from app.backend_common.utils.sanic_wrapper.constants.http import STATUS_CODE_MAPPING, HTTPStatusCodes
from app.backend_common.utils.sanic_wrapper.ctx import app_ctx
from app.backend_common.utils.sanic_wrapper.types import ErrorResponseDict, ResponseDict
from app.backend_common.utils.sanic_wrapper.utils import legacy


def send_response(
    data: t.Any | None = None,
    status_code: int = HTTPStatusCodes.SUCCESS.value,
    *,
    status_mapping: bool = True,
    meta: t.Any | None = None,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
    purge_response_keys: bool = False,
) -> ResponseDict | response.JSONResponse:
    """Construct a JSON response.

    This function is used to create a JSON response for the given data and status code.
    It can also handle custom response bodies, headers, and metadata.

    Args:
        data (t.Any | None): The main data to include in the response. Defaults to None.
        status_code (int): The HTTP status code for the response. Defaults to 200.
        status_mapping (bool): Flag to enable custom HTTP status code mapping. Defaults to True.
        meta (t.Any | None): Additional metadata to include in the response. Defaults to None.
        body (dict | None): Custom response body. If provided, it will be used as the response body. Defaults to None.
        headers (dict[str, str] | None): Custom headers to include in the response. Defaults to None.
        purge_response_keys (bool): Flag to return only the data dictionary without wrapping it in a JSON response. Defaults to False.

    Returns:
        ResponseDict | response.JSONResponse: The constructed JSON response or the data dictionary if purge_response_keys is True.
    """  # noqa: E501

    # NOTE: this is mainly a legacy artefact &
    # requires a dict which has a ``status_code`` key
    if body is not None:
        return response.json(body=body, status=body["status_code"])

    if status_mapping:
        # Map the status code using the custom status code mapping
        status_code = STATUS_CODE_MAPPING.get(status_code, status_code)

    # Construct the response data dictionary
    data: ResponseDict = {
        "data": data,
        "is_success": True,
        "status_code": status_code,
    }

    if meta:
        data["meta"] = meta

    # FIXME: this needs better documentation
    if purge_response_keys:
        # return only the data dictionary if purge_response_keys is True
        return data

    # Return the constructed JSON response with the specified headers
    return response.json(body=data, status=status_code, headers=headers)


async def serialise(handler, *, status_mapping: bool = True):
    """Decorate to serialise the handler response using `send_response`.

    Example:

        ```python
        @app.route("/labs", methods=["GET"])
        @serialise(status_mapping=False)
        async def my_handler(request):
            data = await process_request(request)
            return data
        ```

    """

    @functools.wraps(handler)
    async def wrapper(*args, **kwargs):
        retval = await handler(*args, **kwargs)
        return send_response(retval, status_mapping=status_mapping)

    return wrapper


# ---------------------------------------------------------------------------- #
#                                Error Response                                #
# ---------------------------------------------------------------------------- #


def send_error_response(
    error: str | dict,
    status_code: int,
    meta: t.Any = None,
    error_id: t.Any = None,
    error_code: int = None,
    custom_http_codes_mapping_enabled: bool = True,
) -> response.JSONResponse:
    """Construct an error response.

    Args:
        error (str): The error message or error details.
        status_code (int): The HTTP status code for the response.
        meta (Any, optional): Additional metadata to include in the response. Defaults to None.
        error_id (Any, optional): Error id to lookup against `error_content` dictionary, if attached to app context. Defaults to None.
        custom_http_codes_mapping_enabled (bool, optional): Flag to enable custom HTTP status code mapping. Defaults to True.

    Returns:
        response.JSONResponse: The constructed JSON response containing the error details.
    """  # noqa: E501

    if custom_http_codes_mapping_enabled:
        # map the status code using the custom mapping if enabled
        status_code = STATUS_CODE_MAPPING.get(status_code, status_code)

    if not isinstance(error, dict):
        # Initialize an empty list to hold error details
        error_list = []
        error_content = None

        if error_id:
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

        # construct the error dictionary
        error = {
            "message": error,
            "errors": error_list,
        }

    # construct the final response dictionary
    retval: ErrorResponseDict = {
        "is_success": False,
        "status_code": status_code,
        "error": error,
    }

    if error_code:
        retval["error_code"] = error_code

    if meta:
        retval["meta"] = meta

    return response.json(body=retval, status=status_code)


get_error_body_response = send_error_response
"""Aliased."""


def exception_response(
    exception: Exception,
    /,
    error: str | dict | None = None,
    status_code: int | None = None,
    *,
    meta: t.Any = None,
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

    return response.json(body=retval, status=status_code)


# ---------------------------------------------------------------------------- #


# TODO: consider deprecation
@legacy
def send_response_contracts(body):
    """
    :param response: success / failure response from contract of 1mgmodels
    :return sanic json
    """
    return response.json(body=body, status=response["status_code"])
