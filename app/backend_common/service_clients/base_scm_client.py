from __future__ import annotations

import typing as t

from deputydev_core.clients.http.base_http_client import BaseHTTPClient
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.exception import RefreshTokenFailed
from app.backend_common.exception.exception import RateLimitError
from app.backend_common.services.credentials import AuthHandler


class BaseSCMClient(BaseHTTPClient):
    def __init__(self, auth_handler: AuthHandler):
        super().__init__()
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
        skip_auth_headers: bool = False,
    ):
        # -- prep headers --
        headers = headers or {}
        if not skip_auth_headers:
            auth_headers = await self.auth_headers()
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
            if not skip_auth_headers:
                auth_headers = await self.auth_headers()
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
                f"service request failed with status code {response.status_code} and error {await response.json()}"
            )

        return response

    async def auth_headers(self) -> dict:
        access_token = await self.auth_handler.access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        return headers

    async def get_ws_token_headers(self):
        if not self.workspace_token_headers:
            dd_workspace_id = get_context_value("dd_workspace_id")
            workspace_token = await AuthHandler.get_workspace_access_token(dd_workspace_id)
            self.workspace_token_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {workspace_token}",
            }
        return self.workspace_token_headers
