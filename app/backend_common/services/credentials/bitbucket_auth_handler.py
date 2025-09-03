from __future__ import annotations

from datetime import datetime
from typing import Tuple

from git.util import Actor
from typing_extensions import override

from app.backend_common.service_clients.oauth import BitbucketOAuthClient
from app.backend_common.utils.sanic_wrapper import CONFIG

from .auth_handler import AuthHandler


class BitbucketAuthHandler(AuthHandler):
    __integration__ = "bitbucket"
    __tokenable_type__ = "integration"

    @override
    async def _authorise(self, auth_code: str) -> Tuple[str, datetime, str]:
        response = await BitbucketOAuthClient.get_access_token(auth_code)
        access_token = response["access_token"]
        expires_in = response["expires_in"]
        refresh_token = response["refresh_token"]

        expires_at = self._expires_at(expires_in)

        return access_token, expires_at, refresh_token

    @override
    async def _refresh(self, refresh_token: str) -> Tuple[str, datetime, str]:
        response = await BitbucketOAuthClient.refresh_access_token(refresh_token)
        access_token = response["access_token"]
        expires_in = response["expires_in"]
        refresh_token = response["refresh_token"]

        expires_at = self._expires_at(expires_in)

        return access_token, expires_at, refresh_token

    @override
    def get_git_actor(self) -> Actor:
        return Actor(
            name=CONFIG.config["GIT_ACTORS"]["BITBUCKET"]["NAME"],
            email=CONFIG.config["GIT_ACTORS"]["BITBUCKET"]["EMAIL"],
        )
