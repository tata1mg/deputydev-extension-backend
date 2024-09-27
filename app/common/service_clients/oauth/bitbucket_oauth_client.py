from __future__ import annotations

from enum import Enum

import requests
from torpedo import CONFIG


class GrantType(str, Enum):
    AUTHORISATION = "authorization_code"
    REFRESH = "refresh_token"


class BitbucketOAuthClient:
    OAUTH2_ENDPOINT = CONFIG.config["BITBUCKET"]["OAUTH2_ENDPOINT"]
    # "https://bitbucket.org/site/oauth2/access_token"

    CLIENT_ID = CONFIG.config["BITBUCKET"]["CLIENT_ID"]
    CLIENT_SECRET = CONFIG.config["BITBUCKET"]["CLIENT_SECRET"]

    @classmethod
    async def get_access_token(cls, code: str) -> dict:
        """Get access token from user's temp code."""
        url = cls.OAUTH2_ENDPOINT

        # Basic HTTP Auth
        auth = (cls.CLIENT_ID, cls.CLIENT_SECRET)

        data = {
            "grant_type": GrantType.AUTHORISATION.value,
            "code": code,
            # "redirect_uri": "https://www.1mg.com/",
        }

        response = requests.post(url=url, auth=auth, data=data)
        content = response.json()
        response.raise_for_status()
        return content

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> str:
        """Get new access token using refresh token."""
        url = cls.OAUTH2_ENDPOINT

        # Basic HTTP Auth
        auth = (cls.CLIENT_ID, cls.CLIENT_SECRET)

        data = {
            "grant_type": GrantType.REFRESH.value,
            "refresh_token": refresh_token,
            # "redirect_uri": "https://www.1mg.com/",
        }

        response = requests.post(url=url, auth=auth, data=data)
        content = response.json()
        response.raise_for_status()
        return content
