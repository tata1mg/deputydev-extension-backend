from __future__ import annotations

from tortoise.transactions import in_transaction

from app.backend_common.service_clients.oauth import AtlassianOAuthClient
from app.main.blueprints.deputy_dev.models.dao.postgres import Integrations
from app.main.blueprints.deputy_dev.models.request import OnboardingRequest

from ......backend_common.services.credentials import JiraAuthHandler
from .base import Integration


class Jira(Integration):
    __name__ = "jira"

    def __init__(self) -> None:
        self.auth_handler: JiraAuthHandler | None = None

    async def integrate(self, payload: OnboardingRequest) -> None:
        integration_row = await self.get_integration(payload.team_id, payload.integration_client)

        self.auth_handler = JiraAuthHandler(
            tokenable_id=integration_row.id,
        )

        # get tokens from oauth provider
        tkn, expiry, refresh_tkn = await self.auth_handler.authorise(auth_code=payload.auth_identifier)

        # update intergation with client id
        cloud_id = await self.get_cloud_id(tkn)

        async with in_transaction(connection_name="default"):
            # update integration with clound id
            await Integrations.filter(id=integration_row.id).update(client_account_id=cloud_id)

            # persist tokens
            await self.auth_handler.dump(tkn, expiry, refresh_tkn)

            await self.mark_connected(integration_row)

    async def get_cloud_id(self, token: str) -> str:
        response = await AtlassianOAuthClient.get_accessible_resources(token)
        cloud_id = response[0]["id"]
        return cloud_id
