from sanic.log import error_logger
from app.backend_common.utils.sanic_wrapper import InterServiceRequestException
from app.backend_common.utils.sanic_wrapper.task import AsyncTaskResponse


class BaseCustomParser:
    """
    This custom parser only checks for status_code to be in range of 200 <= status_code < 300
    This parser is to be used when there is no standardized response expected in response of an API.
    """

    def __init__(self, data, status_code, headers, response_headers_list):
        self._data = data
        self._status_code = status_code
        self._headers = headers
        self._response_headers_list = response_headers_list

    def parse(self):
        if 200 <= self._status_code < 300:
            headers = self._prepare_headers()
            res = AsyncTaskResponse(
                self._data,
                meta=self._data.get("meta", None),
                status_code=self._status_code,
                headers=headers,
            )
            return res
        else:
            error_logger.debug(self._data["error"])
            raise InterServiceRequestException(
                error=self._data["error"],
                status_code=self._data["status_code"],
                meta=self._data.get("meta", None),
            )

    def _prepare_headers(self):
        final_headers = {}
        if self._headers and self._response_headers_list:
            for key in self._response_headers_list:
                final_headers[key] = self._headers[key]
            return final_headers

        return final_headers
