from __future__ import annotations

import asyncio
import typing as t

import aiohttp
import ujson as json
import yarl
from aiohttp.helpers import sentinel
from multidict import MultiDict

from app.backend_common.utils.sanic_wrapper.common_utils import CONFIG
from app.backend_common.utils.sanic_wrapper.constants.headers import CONTENT_TYPE
from app.backend_common.utils.sanic_wrapper.constants.http import HTTPMethod
from app.backend_common.utils.sanic_wrapper.ctx import _task_ctx
from app.backend_common.utils.sanic_wrapper.exceptions import (
    HTTPRequestException,
    HTTPRequestTimeoutException,
)
from app.backend_common.utils.sanic_wrapper.parser import BaseAPIResponseParser
from app.backend_common.utils.sanic_wrapper.response import send_response
from app.backend_common.utils.sanic_wrapper.task import AsyncTaskResponse


class BaseAPIClient:
    _host: str = ""
    _timeout: int = 60  # in seconds

    _parser: type[BaseAPIResponseParser] = BaseAPIResponseParser
    _config: dict = CONFIG.config
    _session: aiohttp.ClientSession | None = None

    __interservice__: bool = True

    @classmethod
    async def request(
        cls,
        method: str,
        path: str,
        data: t.Any = None,
        query_params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        multipart: bool = False,
        response_headers_list: list[str] | None = None,
        purge_response_keys: bool = False,
        **kwargs,
    ) -> AsyncTaskResponse:
        # prepare request params
        url = f"{cls._host}{path}"

        if query_params:
            url = cls.prepare_params(url, query_params)

        headers = headers or {}
        headers = cls.prepare_headers(headers, multipart=multipart)

        if data and not multipart:
            data = json.dumps(data)

        # WORKAROUND: if None is passed, the session wide timeout will not be considered
        timeout = timeout or sentinel

        session: aiohttp.ClientSession = await cls._get_session()

        try:
            async with session.request(
                method,
                url,
                data=data,
                headers=headers,
                timeout=timeout,
                **kwargs,
            ) as response:
                resp_status_code = response.status
                resp_headers = response.headers

                try:
                    payload = await response.json()
                except aiohttp.ContentTypeError:
                    payload = await response.text()
                    payload = json.loads(payload)

        except asyncio.TimeoutError as err:
            exception_message = "Inter service request timeout error"
            raise HTTPRequestTimeoutException({"message": exception_message}) from err

        except Exception as err:
            exception_message = str(err)
            raise HTTPRequestException({"message": exception_message}) from err

        if purge_response_keys:
            payload = send_response(
                data=payload,
                status_code=resp_status_code,
                purge_response_keys=purge_response_keys,
            )

        retval = cls._parse_response(
            payload,
            resp_status_code,
            resp_headers,
            response_headers_list,
        )

        return retval

    @classmethod
    def prepare_headers(
        cls,
        headers: dict[str, str],
        *,
        interservice: bool = True,
        multipart: bool = False,
    ) -> dict[str, str]:
        if interservice:
            headers.update(_task_ctx.global_headers)

        if multipart:
            headers[CONTENT_TYPE] = "multipart/form-data"
        else:
            headers[CONTENT_TYPE] = "application/json"

        return headers

    @classmethod
    def prepare_params(cls, url: str, query_params: dict | None) -> str:
        """
        Prepare and append query parameters to the given URL.

        It handles various data types for the query parameters, including boolean values
        and lists.

        Args:
            url (str): The base url to which query parameters will be appended.
            query_params (dict | None): A dictionary of query parameters to be appended to the URL.

        Returns:
            str: The url with the appended query parameters.

        Example:
            ```python
            url = "http://example.com/api"
            query_params = {"search": "test", "page": 2, "active": True, "tags": ["python", "code"]}

            prepared_url = prepare_params(url, query_params)
            ```

            Result will be "http://example.com/api?search=test&page=2&active=true&tags[]=python&tags[]=code"

        """  # noqa: E501
        url = yarl.URL(url)
        query = MultiDict(url.query)

        params = []
        for key, value in query_params.items():
            if isinstance(value, bool):
                # Convert boolean values to their string equivalents
                value = "true" if value else "false"
            if value is not None:
                if isinstance(value, list):
                    # Handle list values by appending '[]' to the key and adding each list item # noqa: E501
                    array_key = key + "[]"
                    for val in value:
                        params.append((array_key, str(val)))
                else:
                    # Convert other types to their string representations
                    params.append((key, str(value)))

        url2 = url.with_query(params)
        query.extend(url2.query)
        url = url.with_query(query)
        url = url.with_fragment(None)

        return str(url)

    @classmethod
    async def _get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None:
            cls._session = await cls.create_session()

        return cls._session

    @classmethod
    async def create_session(cls) -> aiohttp.ClientSession:
        """Create aiohttp client session.
        Override this method to customise session creation.

        Returns:
            aiohttp.ClientSession: New aiohttp client session.
        """
        connector = aiohttp.TCPConnector(
            limit=cls._config.get("CONCURRENCY_LIMIT", 0),
            limit_per_host=cls._config.get("CONCURRENCY_LIMIT_HOST", 0),
            ttl_dns_cache=cls._config.get("TTL_DNS_CACHE", 10),
        )
        timeout = aiohttp.ClientTimeout(total=cls._timeout)
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return session

    @classmethod
    def _parse_response(cls, response, status_code, headers, response_headers_list):
        # a parser is being created every time...
        parser = cls._parser(response, status_code, headers, response_headers_list)
        return parser.parse()

    # ---------------------------------------------------------------------------- #
    #                                 HTTP Methods                                 #
    # ---------------------------------------------------------------------------- #

    @classmethod
    async def get(
        cls,
        path: str,
        data: t.Any = None,
        query_params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        multipart: bool = False,
        response_headers_list: list[str] | None = None,
        purge_response_keys: bool = False,
    ) -> AsyncTaskResponse:
        result = await cls.request(
            HTTPMethod.GET.value,
            path,
            data=data,
            query_params=query_params,
            timeout=timeout,
            headers=headers,
            multipart=multipart,
            response_headers_list=response_headers_list,
            purge_response_keys=purge_response_keys,
        )
        return result

    @classmethod
    async def post(
        cls,
        path: str,
        data: t.Any = None,
        query_params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        multipart: bool = False,
        response_headers_list: list[str] | None = None,
        purge_response_keys: bool = False,
    ) -> AsyncTaskResponse:
        result = await cls.request(
            HTTPMethod.POST.value,
            path,
            data=data,
            query_params=query_params,
            timeout=timeout,
            headers=headers,
            multipart=multipart,
            response_headers_list=response_headers_list,
            purge_response_keys=purge_response_keys,
        )
        return result

    @classmethod
    async def put(
        cls,
        path: str,
        data: t.Any = None,
        query_params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        multipart: bool = False,
        response_headers_list: list[str] | None = None,
        purge_response_keys: bool = False,
    ) -> AsyncTaskResponse:
        result = await cls.request(
            HTTPMethod.PUT.value,
            path,
            data=data,
            query_params=query_params,
            timeout=timeout,
            headers=headers,
            multipart=multipart,
            response_headers_list=response_headers_list,
            purge_response_keys=purge_response_keys,
        )
        return result

    @classmethod
    async def patch(
        cls,
        path: str,
        data: t.Any = None,
        query_params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        multipart: bool = False,
        response_headers_list: list[str] | None = None,
        purge_response_keys: bool = False,
    ) -> AsyncTaskResponse:
        result = await cls.request(
            HTTPMethod.PATCH.value,
            path,
            data=data,
            query_params=query_params,
            timeout=timeout,
            headers=headers,
            multipart=multipart,
            response_headers_list=response_headers_list,
            purge_response_keys=purge_response_keys,
        )
        return result

    @classmethod
    async def delete(
        cls,
        path: str,
        data: t.Any = None,
        query_params: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        multipart: bool = False,
        response_headers_list: list[str] | None = None,
        purge_response_keys: bool = False,
    ) -> AsyncTaskResponse:
        result = await cls.request(
            HTTPMethod.DELETE.value,
            path,
            data=data,
            query_params=query_params,
            timeout=timeout,
            headers=headers,
            multipart=multipart,
            response_headers_list=response_headers_list,
            purge_response_keys=purge_response_keys,
        )
        return result


class SanicClient(BaseAPIClient):
    _config: dict = CONFIG.config
    _health_check_config: dict = _config.get("HEALTH_CHECK", {})
    _port: str = _config.get("PORT")
    _hostname: str = _config.get("HOST")
    _host: str = f"http://{_hostname}:{_port}"
    _timeout: int = _health_check_config.get("TIMEOUT", 1)
