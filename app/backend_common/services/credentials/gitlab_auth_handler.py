from __future__ import annotations

from datetime import datetime
from typing import Tuple

from typing_extensions import override

from app.backend_common.service_clients.oauth import GitlabOAuthClient

from .auth_handler import AuthHandler


class GitlabAuthHandler(AuthHandler):
    __integration__ = "gitlab"
    __tokenable_type__ = "integration"

    @override
    async def _authorise(self, auth_code: str) -> Tuple[str, datetime, str]:
        response = await GitlabOAuthClient.get_access_token(auth_code)
        access_token = response["access_token"]
        expires_in = response["expires_in"]
        refresh_token = response["refresh_token"]

        expires_at = self._expires_at(expires_in)

        return access_token, expires_at, refresh_token

    @override
    async def _refresh(self, refresh_token: str) -> Tuple[str, datetime, str]:
        response = await GitlabOAuthClient.refresh_access_token(refresh_token)
        access_token = response["access_token"]
        expires_in = response["expires_in"]
        refresh_token = response["refresh_token"]

        expires_at = self._expires_at(expires_in)

        return access_token, expires_at, refresh_token
