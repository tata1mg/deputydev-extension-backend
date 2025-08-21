from __future__ import annotations

from typing import Any, Dict, List

from sanic.log import logger
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from app.backend_common.exception.exception import OnboardingError
from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.service_clients.bitbucket import BitbucketWorkspaceClient
from app.main.blueprints.deputy_dev.models.dao.postgres import Integrations
from app.main.blueprints.deputy_dev.models.request import OnboardingRequest

from ......backend_common.services.credentials import BitbucketAuthHandler
from .base import SCM, Integration


class Bitbucket(Integration, SCM):
    __name__ == "bitbucket"

    def __init__(self, auth_handler: BitbucketAuthHandler | None = None) -> None:
        self.auth_handler: BitbucketAuthHandler | None = auth_handler
        self.client: BitbucketWorkspaceClient | None = None

    async def integrate(self, payload: OnboardingRequest) -> None:
        integration_row: Integrations = await self.get_integration(
            team_id=payload.team_id, client=payload.integration_client
        )

        self.auth_handler: BitbucketAuthHandler = BitbucketAuthHandler(tokenable_id=integration_row.id)

        # get tokens from oauth provider
        tkn, expiry, refresh_tkn = await self.auth_handler.authorise(auth_code=payload.auth_identifier)

        self.client = BitbucketWorkspaceClient(auth_handler=self.auth_handler)

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
            await self.create_webhooks(workspace["slug"], workspace["id"])

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

    async def create_webhooks(self, workspace_slug: str, scm_workspace_id: str) -> None:
        set_hooks = await self.list_all_webhooks(workspace_slug)

        filtered_hooks = []
        for webhook in self.WEBHOOKS_PAYLOAD:
            # -- filter --
            if self.__hook_exists(webhook, set_hooks):
                logger.info("Skipping already set hook")
                continue
            filtered_hooks.append(webhook)

        for webhook in filtered_hooks:
            url = self._prepare_url(
                base_url=webhook["URL"],
                vcs_type="bitbucket",
                scm_workspace_id=scm_workspace_id,
            )

            await self.client.create_webhooks(
                workspace_slug,
                description=webhook["DESCRIPTION"],
                webhook_url=url,
                events=webhook["EVENTS"]["BITBUCKET"],
                secret_token=webhook["SECRET_TOKEN"],
            )
            logger.info("Created new webhook")

        return filtered_hooks

    def __hook_exists(self, new_webhook: Dict[str, Any], set_hooks: List[Dict[str, Any]]) -> bool:
        for set_hook in set_hooks:
            if set_hook["active"]:
                url = set_hook["url"]
                new_url = self._prepare_url(new_webhook["URL"], vcs_type="bitbucket")
                if new_url == url:
                    if set(new_webhook["EVENTS"]["BITBUCKET"]) == set(set_hook["events"]):
                        return True

        return False

    async def list_all_workspaces(self) -> List[Dict[str, Any]]:
        resp = await self.client.get_all_workspaces()
        user_workspaces = resp["values"]

        result: List[Dict[str, Any]] = []
        for user_workspace in user_workspaces:
            if not user_workspace["permission"] == "owner":
                logger.info("Skipping workspace : Not owner")
                continue

            workspace_info = user_workspace["workspace"]

            workspace_data = {
                "id": workspace_info["uuid"],
                "name": workspace_info["name"],
                "slug": workspace_info["slug"],
            }
            result.append(workspace_data)

        logger.info("Workspaces with ownership: %s", result)
        return result

    async def list_all_webhooks(self, workspace: str) -> List[Dict[str, Any]]:
        resp = await self.client.get_webhooks(workspace)
        workspace_webhooks = resp["values"]

        result = []
        for hook in workspace_webhooks:
            webhook_info = {
                "url": hook["url"],
                "events": hook["events"],
                "active": hook["active"],
            }
            result.append(webhook_info)

        return result
