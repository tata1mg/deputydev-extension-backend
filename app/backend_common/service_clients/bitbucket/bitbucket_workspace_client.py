from __future__ import annotations

from typing import Any, Dict

from app.backend_common.services.credentials import AuthHandler
from app.backend_common.utils.sanic_wrapper import CONFIG

from ..base_scm_client import BaseSCMClient


class BitbucketWorkspaceClient(BaseSCMClient):
    def __init__(self, auth_handler: AuthHandler) -> None:
        self.bitbucket_url = CONFIG.config["BITBUCKET"]["URL"]

        super().__init__(auth_handler=auth_handler)

    async def get_all_workspaces(self) -> Dict[str, Any]:
        url = f"{self.bitbucket_url}/2.0/user/permissions/workspaces"
        response = await self.get(url=url)
        response.raise_for_status()
        return await response.json()

    # ---------------------------------------------------------------------------- #

    async def get_webhooks(self, workspace: str) -> Dict[str, Any]:
        url = f"{self.bitbucket_url}/2.0/workspaces/{workspace}/hooks"
        response = await self.get(url=url)
        response.raise_for_status()
        return await response.json()

    async def create_webhooks(
        self,
        workspace: str,
        description: str,
        webhook_url: str,
        events: list[str],
        secret_token: str,
    ) -> Dict[str, Any]:
        url = f"{self.bitbucket_url}/2.0/workspaces/{workspace}/hooks"

        data: Dict[str, Any] = {
            "description": description,
            "url": webhook_url,
            "active": True,
            "events": events,
            "secret": secret_token,
        }

        response = await self.post(url=url, json=data)
        response.raise_for_status()
        return await response.json()

    async def get_active_users(self, workspace: str) -> Dict[str, Any]:
        url = f"{self.bitbucket_url}/2.0/workspaces/{workspace}/members"
        response = await self.get(url)
        response.raise_for_status()
        return await response.json()

    async def get_all_repos(self, workspace: str) -> Dict[str, Any]:
        url = f"{self.bitbucket_url}/2.0/repositories/{workspace}"
        response = await self.get(url)
        response.raise_for_status()
        return await response.json()
