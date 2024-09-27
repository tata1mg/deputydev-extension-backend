from __future__ import annotations

from typing_extensions import override

from app.common.service_clients.oauth import BitbucketOAuthClient

from .auth_handler import AuthHandler


class BitbucketAuthHandler(AuthHandler):
    __integration__ = "bitbucket"
    __tokenable_type__ = "integration"

    @override
    async def _authorise(self, auth_code):
        response = await BitbucketOAuthClient.get_access_token(auth_code)
        access_token = response["access_token"]
        expires_in = response["expires_in"]
        refresh_token = response["refresh_token"]

        expires_at = self._expires_at(expires_in)

        return access_token, expires_at, refresh_token

    @override
    async def _refresh(self, refresh_token):
        response = await BitbucketOAuthClient.refresh_access_token(refresh_token)
        access_token = response["access_token"]
        expires_in = response["expires_in"]
        refresh_token = response["refresh_token"]

        expires_at = self._expires_at(expires_in)

        return access_token, expires_at, refresh_token
