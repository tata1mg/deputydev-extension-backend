from app.backend_common.utils.sanic_wrapper import CONFIG
from typing_extensions import override

from ..base_scm_client import BaseSCMClient


class GithubClient(BaseSCMClient):
    BASE_URL = CONFIG.config["GITHUB"]["HOST"]

    @override
    async def auth_headers(self) -> dict:
        access_token = await self.auth_handler.access_token()
        headers = {
            "Content-Type": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        return headers

    async def get_org_webhooks(self, org_name):
        url = f"{self.BASE_URL}/orgs/{org_name}/hooks"
        response = await self.get(url=url)
        response.raise_for_status()
        return await response.json()

    async def create_org_webhook(self, org_name, webhook_url, events, secret):
        url = f"{self.BASE_URL}/orgs/{org_name}/hooks"

        data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "secret": secret,
                "content_type": "json",
            },
        }

        response = await self.post(url=url, json=data)
        content = await response.json()
        response.raise_for_status()
        return content
