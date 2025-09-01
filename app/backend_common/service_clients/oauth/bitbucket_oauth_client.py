from __future__ import annotations

from enum import Enum

from aiohttp import BasicAuth
from deputydev_core.clients.http.base_http_session_manager import SessionManager

from app.backend_common.utils.sanic_wrapper import CONFIG


class GrantType(str, Enum):
    AUTHORISATION = "authorization_code"
    REFRESH = "refresh_token"


class BitbucketOAuthClient:
    OAUTH2_ENDPOINT = CONFIG.config["BITBUCKET"]["OAUTH2_ENDPOINT"]

    CLIENT_ID = CONFIG.config["BITBUCKET"]["CLIENT_ID"]
    CLIENT_SECRET = CONFIG.config["BITBUCKET"]["CLIENT_SECRET"]
    SESSION_MANAGER = SessionManager()

    @classmethod
    async def get_access_token(cls, code: str) -> dict:
        """Get access token from user's temp code."""
        url = cls.OAUTH2_ENDPOINT

        # Basic HTTP Auth
        auth = BasicAuth(cls.CLIENT_ID, cls.CLIENT_SECRET)

        data = {
            "grant_type": GrantType.AUTHORISATION.value,
            "code": code,
        }
        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, auth=auth, data=data) as response:
            response.raise_for_status()
            return await response.json()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> str:
        """Get new access token using refresh token."""
        url = cls.OAUTH2_ENDPOINT

        # Basic HTTP Auth
        auth = BasicAuth(cls.CLIENT_ID, cls.CLIENT_SECRET)

        data = {
            "grant_type": GrantType.REFRESH.value,
            "refresh_token": refresh_token,
        }
        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, auth=auth, data=data) as response:
            response.raise_for_status()
            return await response.json()
