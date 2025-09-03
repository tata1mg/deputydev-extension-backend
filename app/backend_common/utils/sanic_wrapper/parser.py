from sanic.log import error_logger

from app.backend_common.utils.sanic_wrapper.exceptions import InterServiceRequestException
from app.backend_common.utils.sanic_wrapper.task import AsyncTaskResponse


class BaseAPIResponseParser:
    def __init__(self, data, status_code, headers, response_headers_list):
        self._data = data
        self._status_code = status_code
        self._headers = headers
        self._response_headers_list = response_headers_list

    def parse(self) -> AsyncTaskResponse:
        if self._data.get("is_success"):
            headers = self._prepare_headers()
            return AsyncTaskResponse(
                self._data["data"],
                meta=self._data.get("meta", None),
                status_code=self._data["status_code"],
                headers=headers,
            )

        error = self._data.get("error") or self._data.get("errors")
        error_logger.debug(error)
        raise InterServiceRequestException(
            error=error,
            status_code=self._data.get("status_code") or self._status_code,
            error_code=self._data.get("error_code"),
            meta=self._data.get("meta", None),
        )

    def _prepare_headers(self):
        final_headers = {}
        if self._headers and self._response_headers_list:
            for key in self._response_headers_list:
                final_headers[key] = self._headers[key]
            return final_headers

        return final_headers
