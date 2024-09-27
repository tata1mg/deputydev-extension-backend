from __future__ import annotations

from enum import Enum

import requests
from torpedo import CONFIG


class GrantType(str, Enum):
    AUTHORISATION = "authorization_code"
    REFRESH = "refresh_token"


class GitlabOAuthClient:
    OAUTH2_ENDPOINT = CONFIG.config["GITLAB"]["OAUTH2_ENDPOINT"]
    # e.g. "https://gitlab.example.com/oauth/token"

    CLIENT_ID = CONFIG.config["GITLAB"]["CLIENT_ID"]
    CLIENT_SECRET = CONFIG.config["GITLAB"]["CLIENT_SECRET"]

    REDIRECT_URL = "https://1mg.com"

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

        response = requests.post(url=url, json=data)
        content = response.json()
        response.raise_for_status()

        # parse for token

        # e.g. resp
        # {
        #     "access_token": "***REMOVED***",
        #     "token_type": "bearer",
        #     "expires_in": 7200,
        #     "refresh_token": "***REMOVED***",
        #     "created_at": 1607635748,
        # }

        return content

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

        response = requests.post(url, json=data)
        content = response.json()
        response.raise_for_status()

        # e.g. resp
        # {
        #     "access_token": "***REMOVED***",
        #     "token_type": "bearer",
        #     "expires_in": 7200,
        #     "refresh_token": "***REMOVED***",
        #     "created_at": 1628711391,
        # }

        return content
