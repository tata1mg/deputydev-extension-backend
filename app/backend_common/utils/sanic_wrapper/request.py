from __future__ import annotations

import typing as t
import uuid
from functools import cached_property

import sanic

from app.backend_common.utils.sanic_wrapper.constants.headers import (
    X_REQUEST_ID,
    X_SERVICE_NAME,
    X_SOURCE_IP,
    X_SOURCE_REFERER,
    X_SOURCE_USER_AGENT,
    X_VISITOR_ID,
)
from app.backend_common.utils.sanic_wrapper.exceptions import JsonDecodeException


class SanicRequest(sanic.Request):
    """Custom request class for Sanic, extending Sanic's Request.

    Provides additional methods for handling request parameters and JSON data.
    """

    def parse_params(self) -> dict:
        """Get all query params and `match_info` params as query params.

        Returns:
            dict: A dictionary of query params and `match_info` params.

        """
        params = {}
        # Iterate through query parameters
        for key, value in self.args.items():
            modified_key = key.replace("[]", "")  # Remove '[]' suffix for array parameters
            if "[]" in key:  # Check if the parameter is an array
                params[modified_key] = value  # Store the value as a list
            else:
                params[key] = (
                    value if len(value) > 1 else value[0]
                )  # Store the value or the first value if there are multiple

        # Store match_info parameters as is
        for key, value in self.match_info.items():
            params[key] = value

        return params

    request_params = parse_params
    """Alias for compatibility with older versions."""

    def parse_json(self) -> t.Any:
        """Parse body as JSON.

        Raises:
            JsonDecodeException: If the request body is not JSON or cannot be decoded.

        Returns:
            t.Any: The request body as JSON.

        """
        data = self.json
        if data is None:
            raise JsonDecodeException("Invalid Request")  # FIXME: imporve error message
        return data

    custom_json = parse_json
    """Alias for compatibility with older versions."""

    @cached_property
    def req_id(self) -> str:
        """A unique request ID.

        Checks if the request headers contain a unique request ID.
        If not, it generates a new UUID and returns it as a string. This ensures that every
        request has a unique identifier for tracking and logging purposes.

        Returns:
            str: The unique request ID as a string.
        """  # noqa: E501
        return self.headers.get(X_REQUEST_ID) or str(uuid.uuid4())

    @cached_property
    def interservice_headers(self) -> dict:
        """Interservice headers common accross platform.

        Extracts and returns a dictionary of global headers from the request.

        This function extracts specific headers from the request which can later
        be sent in all outgoing api calls.

        Returns:
            dict: A dictionary containing the global headers.
        """
        return {
            X_SERVICE_NAME: self.app.name,
            X_REQUEST_ID: self.req_id,
            X_VISITOR_ID: self.headers.get(X_VISITOR_ID, ""),
            X_SOURCE_IP: self.headers.get(X_SOURCE_IP, ""),
            X_SOURCE_USER_AGENT: self.headers.get(X_SOURCE_USER_AGENT, ""),
            X_SOURCE_REFERER: self.headers.get(X_SOURCE_REFERER, ""),
        }


Request = SanicRequest
"""We alias this for ease of type hints.
Ideally services should import this and
use as type hint for request param in the handler.

Example:
    ```py
    from app.backend_common.utils.sanic_wrapper import Request

    @bp.route(...)
    async def index(request: Request):
        ...
    ```
"""
