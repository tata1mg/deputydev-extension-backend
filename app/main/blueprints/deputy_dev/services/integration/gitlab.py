from __future__ import annotations

from sanic.log import logger
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from app.backend_common.exception.exception import OnboardingError
from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.service_clients.gitlab.gitlab_group_client import (
    GitlabGroupClient,
)
from app.main.blueprints.deputy_dev.models.dao.postgres import Integrations
from app.main.blueprints.deputy_dev.models.request import OnboardingRequest

from ......backend_common.services.credentials import GitlabAuthHandler
from .base import SCM, Integration


class Gitlab(Integration, SCM):
    __name__ = "gitlab"

    def __init__(self, auth_handler: GitlabAuthHandler | None = None) -> None:
        self.auth_handler: GitlabAuthHandler | None = auth_handler
        self.client: GitlabGroupClient | None = None

    async def integrate(self, payload: OnboardingRequest):
        integration_row: Integrations = await self.get_integration(
            team_id=payload.team_id, client=payload.integration_client
        )

        self.auth_handler: GitlabAuthHandler = GitlabAuthHandler(
            tokenable_id=integration_row.id,
        )

        # get tokens from oauth provider
        tkn, expiry, refresh_tkn = await self.auth_handler.authorise(auth_code=payload.auth_identifier)

        self.client = GitlabGroupClient(auth_handler=self.auth_handler)

        workspaces_to_onboard = set(payload.workspaces)
        all_workspaces = await self.list_all_workspaces()

        filtered_workspaces = []
        for workspace in all_workspaces:
            if workspace["slug"] in workspaces_to_onboard:
                try:
                    await Workspaces.get(slug=workspace["slug"])
                except DoesNotExist:
                    filtered_workspaces.append(workspace)
                else:
                    raise OnboardingError(f"Workspace {workspace['slug']} already exists!")

        if len(filtered_workspaces) == 0:
            raise OnboardingError("No supplied workspaces match present workspaces")

        logger.info("Filtered Workspaces: %s", filtered_workspaces)

        for workspace in filtered_workspaces:
            group_id = workspace["id"]
            await self.create_webhooks(group_id)

        async with in_transaction(connection_name="default"):
            for workspace in filtered_workspaces:
                await Workspaces.create(
                    name=workspace["name"],
                    slug=workspace["slug"],
                    scm_workspace_id=workspace["id"],
                    integration_id=integration_row.id,
                    scm=payload.integration_client,
                    team_id=payload.team_id,
                )

            await self.auth_handler.dump(tkn, expiry, refresh_tkn)

            await self.mark_connected(integration_row)

    async def create_webhooks(self, group_id):
        set_hooks = await self.list_all_webhooks(group_id)

        filtered_hooks = []
        for webhook in self.WEBHOOKS_PAYLOAD:
            # -- filter --
            if self.__hook_exists(webhook, set_hooks):
                logger.info("Skipping already set hook")
                continue
            filtered_hooks.append(webhook)

        for webhook in filtered_hooks:
            events_dict = self.__prepare_events_dict(webhook["EVENTS"]["GITLAB"])

            scm_workspace_id = group_id
            url = self._prepare_url(
                base_url=webhook["URL"],
                vcs_type="gitlab",
                scm_workspace_id=scm_workspace_id,
            )

            await self.client.create_webhooks(
                group_id=group_id,
                name=webhook["NAME"],
                description=webhook["DESCRIPTION"],
                webhook_url=url,
                events_dict=events_dict,
                token=webhook["SECRET_TOKEN"],
            )

        return filtered_hooks

    def __hook_exists(self, new_webhook, set_hooks):
        for set_hook in set_hooks:
            url = set_hook["url"]
            new_url = self._prepare_url(new_webhook["URL"], vcs_type="gitlab")
            if new_url == url:
                if set(new_webhook["EVENTS"]["GITLAB"]) == set(set_hook["events"]):
                    return True

        return False

    def __prepare_events_dict(self, events_list: list[str]):
        events = set(events_list)

        events_dict = {}
        if "pull_requests" in events:
            events_dict["merge_requests_events"] = True

        if "comments" in events:
            events_dict["note_events"] = True

        return events_dict

    async def list_all_workspaces(self):
        resp = await self.client.get_all_groups()
        groups = resp

        result = []
        for group in groups:
            result.append(
                {
                    "id": group["id"],
                    "name": group["name"],
                    "slug": group["path"],
                }
            )

        return result

    async def list_all_webhooks(self, group_id):
        resp = await self.client.get_group_webhooks(group_id)
        set_hooks = resp

        result = []
        for hook in set_hooks:
            events = []
            if hook["merge_requests_events"]:
                events.append("pull_requests")
            if hook["note_events"]:
                events.append("comments")

            result.append({"url": hook["url"], "events": events})
        return result
