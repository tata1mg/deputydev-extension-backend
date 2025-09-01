from __future__ import annotations

from enum import Enum

from deputydev_core.clients.http.base_http_session_manager import SessionManager

from app.backend_common.utils.sanic_wrapper import CONFIG


class GrantType(str, Enum):
    AUTHORISATION = "authorization_code"
    REFRESH = "refresh_token"


class GitlabOAuthClient:
    OAUTH2_ENDPOINT = CONFIG.config["GITLAB"]["OAUTH2_ENDPOINT"]
    # e.g. "https://gitlab.example.com/oauth/token"

    CLIENT_ID = CONFIG.config["GITLAB"]["CLIENT_ID"]
    CLIENT_SECRET = CONFIG.config["GITLAB"]["CLIENT_SECRET"]

    REDIRECT_URL = "https://1mg.com"
    SESSION_MANAGER = SessionManager()

    @classmethod
    async def get_access_token(cls, code: str) -> str:
        """Get access token from user's temp code."""
        url = cls.OAUTH2_ENDPOINT

        data = {
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "code": code,
            "grant_type": GrantType.AUTHORISATION.value,
            "redirect_uri": cls.REDIRECT_URL,
        }

        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, json=data) as response:
            response.raise_for_status()
            return await response.json()

        # parse for token

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> str:
        """Get new access token using refresh token."""
        url = cls.OAUTH2_ENDPOINT

        data = {
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": GrantType.REFRESH.value,
            "redirect_uri": cls.REDIRECT_URL,
        }

        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, json=data) as response:
            response.raise_for_status()
            return await response.json()
