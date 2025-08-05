from __future__ import annotations

from sanic.log import logger
from tortoise.transactions import in_transaction

from app.backend_common.exception.exception import OnboardingError
from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.service_clients.github.github_client import GithubClient
from app.backend_common.service_clients.oauth import GithubOAuthClient
from app.main.blueprints.deputy_dev.models.request import OnboardingRequest

from ......backend_common.services.credentials import GithubAuthHandler
from .base import SCM, Integration


class Github(Integration, SCM):
    __name__ = "github"

    def __init__(self, auth_handler: GithubAuthHandler | None = None) -> None:
        self.auth_handler: GithubAuthHandler | None = auth_handler
        self.client: GithubClient | None = None

    async def integrate(self, payload: OnboardingRequest):
        integration_row = await self.get_integration(team_id=payload.team_id, client=payload.integration_client)

        self.auth_handler = GithubAuthHandler()

        # get tokens from oauth provider
        installation_id = payload.auth_identifier
        tkn, expiry, installation_id = await self.auth_handler.authorise(installation_id=installation_id)

        self.client = GithubClient(auth_handler=self.auth_handler)

        workspace_info = await self.get_workspace(installation_id=installation_id)

        created_hooks = await self.create_webhooks(workspace_info["slug"], workspace_info["scm_workspace_id"])
        if len(created_hooks) == 0:
            raise OnboardingError("No new hooks to create")

        async with in_transaction(connection_name="default"):
            workspace = Workspaces(
                name=workspace_info["name"],
                slug=workspace_info["slug"],
                scm_workspace_id=workspace_info["scm_workspace_id"],
                integration_id=integration_row.id,
                scm=payload.integration_client,
                team_id=payload.team_id,
            )
            await workspace.save()

            self.auth_handler.tokenable_id = workspace.id
            await self.auth_handler.dump(tkn, expiry, installation_id)

            await self.mark_connected(integration_row)

    async def get_workspace(self, installation_id) -> dict:
        response = await GithubOAuthClient.get_installation(installation_id=installation_id)
        account = response["account"]

        return {
            "name": account["login"],
            "slug": account["login"],
            "scm_workspace_id": account["id"],
        }

    async def create_webhooks(self, org_name: str, scm_workspace_id) -> list[dict]:
        set_hooks = await self.list_all_webhooks(org_name)
        filtered_hooks = []
        for webhook in self.WEBHOOKS_PAYLOAD:
            if self.__hook_exists(webhook, set_hooks=set_hooks, scm_workspace_id=scm_workspace_id):
                logger.info("Skipping already set hook")
                continue
            filtered_hooks.append(webhook)

        for webhook in filtered_hooks:
            url = self._prepare_url(
                base_url=webhook["URL"],
                vcs_type="github",
                scm_workspace_id=scm_workspace_id,
            )

            await self.client.create_org_webhook(
                org_name=org_name,
                webhook_url=url,
                events=webhook["EVENTS"]["GITHUB"],
                secret=webhook["SECRET_TOKEN"],
            )
            logger.info("Created new webhook")

        return filtered_hooks

    def __hook_exists(self, new_webhook: dict, set_hooks: list[dict], scm_workspace_id) -> bool:
        #  check with all set hooks
        for set_hook in set_hooks:
            # only consider active hooks
            if set_hook["active"]:
                # matching url sufficient for github hooks
                url = set_hook["config"]["url"]
                new_url = self._prepare_url(new_webhook["URL"], vcs_type="github", scm_workspace_id=scm_workspace_id)
                if url == new_url:
                    return True

        return False

    async def list_all_webhooks(self, org_name: str) -> list[str]:
        response = await self.client.get_org_webhooks(org_name)
        return response

    async def list_all_workspaces(self):
        pass
