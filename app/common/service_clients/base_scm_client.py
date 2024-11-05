from __future__ import annotations

import typing as t

import requests  # TODO: why not aiohttp

from app.common.exception import RefreshTokenFailed
from app.common.exception.exception import RateLimitError
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)


class BaseSCMClient:
    def __init__(self, auth_handler: AuthHandler):
        self.auth_handler: AuthHandler = auth_handler
        self.workspace_token_headers = None

    async def request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        data: t.Any = None,
        json: t.Any = None,
        skip_headers: bool = False,
    ):
        # -- prep headers --
        headers = headers or {}

        if not skip_headers:
            auth_headers = await self._auth_headers()
            headers.update(auth_headers)

        response = await self._request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            data=data,
            json=json,
        )
        if response.status_code == 401:
            # token probably expired
            if not skip_headers:
                auth_headers = await self._auth_headers()
                headers.update(auth_headers)

            response = await self._request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json,
            )

            if response.status_code == 401:
                raise RefreshTokenFailed("Forbidden error even after refreshed token")
        elif response.status_code == 429:
            raise RateLimitError("VCS rate limit breached")

        if response.status_code not in [200, 201, 204]:
            AppLogger.log_warn(
                f"service request failed with status code {response.status_code} and error {response.json()}"
            )

        return response

    async def _auth_headers(self) -> dict:
        access_token = await self.auth_handler.access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        data: t.Any = None,
        json: t.Any = None,
    ):
        response = requests.request(method, url, params=params, headers=headers, data=data, json=json)
        return response

    # ---------------------------------------------------------------------------- #
    #                                 HTTP METHODS                                 #
    # ---------------------------------------------------------------------------- #

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        skip_headers: bool = False,
    ):
        return await self.request("GET", url, params=params, headers=headers, skip_headers=skip_headers)

    async def post(
        self,
        url: str,
        data: t.Any = None,
        json: t.Any = None,
        headers: dict | None = None,
        skip_headers: bool = False,
    ):
        return await self.request("POST", url, headers=headers, data=data, json=json, skip_headers=skip_headers)

    async def put(
        self,
        url: str,
        data: t.Any = None,
        json: t.Any = None,
        headers: dict | None = None,
        skip_headers: bool = False,
    ):
        return await self.request("PUT", url, headers=headers, data=data, json=json, skip_headers=skip_headers)

    async def patch(
        self,
        url: str,
        data: t.Any = None,
        json: t.Any = None,
        headers: dict | None = None,
        skip_headers: bool = False,
    ):
        return await self.request("PATCH", url, headers=headers, data=data, json=json, skip_headers=skip_headers)

    async def get_ws_token_headers(self):
        if not self.workspace_token_headers:
            dd_workspace_id = get_context_value("dd_workspace_id")
            workspace_token = await AuthHandler.get_workspace_access_token(dd_workspace_id)
            self.workspace_token_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {workspace_token}",
            }
        return self.workspace_token_headers
