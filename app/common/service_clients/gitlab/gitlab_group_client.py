from __future__ import annotations

from app.main.blueprints.deputy_dev.services.credentials import AuthHandler

from ..base_scm_client import BaseSCMClient


class GitlabGroupClient(BaseSCMClient):
    def __init__(self, auth_handler: AuthHandler) -> None:
        super().__init__(auth_handler=auth_handler)

    async def get_all_groups(self):
        url = "https://gitlab.com/api/v4/groups/"
        response = await self.get(url)
        response.raise_for_status()
        return await response.json()

    async def get_group_webhooks(self, group_id):
        url = f"https://gitlab.com/api/v4/groups/{group_id}/hooks"
        response = await self.get(url)
        response.raise_for_status()
        return await response.json()

    async def create_webhooks(
        self, group_id, name: str, description: str, webhook_url: str, events_dict: dict, token: str
    ):
        """Add a new group webhook.

        ref: https://docs.gitlab.com/ee/api/group_webhooks.html#add-a-group-hook
        ref: https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html
        """

        url = f"https://gitlab.com/api/v4/groups/{group_id}/hooks"

        data = {"name": name, "description": description, "url": webhook_url, "token": token}

        data.update(events_dict)

        response = await self.post(url=url, json=data)
        response.raise_for_status()
        return await response.json()

    def _get_webhook_events(self, pull_requests: bool):
        return {
            "push_events": True,
            "issues_events": True,
            "merge_requests_events": True,  # all pull request events
            "note_events": True,  # comment events
        }
