"""Confluence & Jira OAuth Client."""

from __future__ import annotations

from typing import Any, Dict

from deputydev_core.clients.http.base_http_session_manager import SessionManager

from app.backend_common.utils.sanic_wrapper import CONFIG


class AtlassianOAuthClient:
    CLIENT_ID = CONFIG.config["ATLASSIAN"]["CLIENT_ID"]
    CLIENT_SECRET = CONFIG.config["ATLASSIAN"]["CLIENT_SECRET"]
    SESSION_MANAGER = SessionManager()

    @classmethod
    async def get_access_token(cls, code: str) -> Dict[str, Any]:
        url = "https://auth.atlassian.com/oauth/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "code": code,
        }

        headers = {"Content-Type": "application/json"}

        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, json=data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        url = "https://auth.atlassian.com/oauth/token"

        data = {
            "grant_type": "refresh_token",
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "refresh_token": refresh_token,
        }

        headers = {"Content-Type": "application/json"}

        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, json=data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    @classmethod
    async def get_accessible_resources(cls, token: str) -> Dict[str, Any]:
        url = "https://api.atlassian.com/oauth/token/accessible-resources"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        session = await cls.SESSION_MANAGER.get_session()
        async with session.get(url=url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
