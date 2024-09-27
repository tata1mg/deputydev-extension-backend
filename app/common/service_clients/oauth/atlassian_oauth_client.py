"""Confluence & Jira OAuth Client."""

from __future__ import annotations

import requests
from torpedo import CONFIG


class AtlassianOAuthClient:
    CLIENT_ID = CONFIG.config["ATLASSIAN"]["CLIENT_ID"]
    CLIENT_SECRET = CONFIG.config["ATLASSIAN"]["CLIENT_SECRET"]

    @classmethod
    async def get_access_token(cls, code: str) -> dict:
        url = "https://auth.atlassian.com/oauth/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "code": code,
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(url=url, json=data, headers=headers)
        content = response.json()
        response.raise_for_status()
        return content

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> dict:
        url = "https://auth.atlassian.com/oauth/token"

        data = {
            "grant_type": "refresh_token",
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "refresh_token": refresh_token,
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(url=url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    async def get_accessible_resources(cls, token):
        url = "https://api.atlassian.com/oauth/token/accessible-resources"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        return response.json()
