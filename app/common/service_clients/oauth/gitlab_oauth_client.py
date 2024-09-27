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
        #     "access_token": "de6780bc506a0446309bd9362820ba8aed28aa506c71eedbe1c5c4f9dd350e54",
        #     "token_type": "bearer",
        #     "expires_in": 7200,
        #     "refresh_token": "8257e65c97202ed1726cf9571600918f3bffb2544b26e00a61df9897668c33a1",
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
        #     "access_token": "c97d1fe52119f38c7f67f0a14db68d60caa35ddc86fd12401718b649dcfa9c68",
        #     "token_type": "bearer",
        #     "expires_in": 7200,
        #     "refresh_token": "803c1fd487fec35562c205dac93e9d8e08f9d3652a24079d704df3039df1158f",
        #     "created_at": 1628711391,
        # }

        return content
