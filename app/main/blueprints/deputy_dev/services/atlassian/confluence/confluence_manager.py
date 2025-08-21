from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.service_clients.confluence.page import Page
from app.main.blueprints.deputy_dev.utils import get_auth_handler

from .confluence_helper import ConfluenceHelper


class ConfluenceManager:
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        self.auth_handler = None
        self.client_account_id = None
        self.is_confluence_integration_enabled = False

    async def set_auth_handler(self) -> None:
        if not self.auth_handler and not self.client_account_id:
            confluence_auth_handler, integration_info = await get_auth_handler(
                client="confluence", team_id=get_context_value("team_id")
            )
            if confluence_auth_handler and integration_info:
                self.auth_handler = confluence_auth_handler
                self.client_account_id = integration_info["client_account_id"]
                self.is_confluence_integration_enabled = True

    async def get_description_text(self) -> str:
        """
        Extracts the Confluence document ID from the given Confluence link.
        Returns:
            str: returns description of confluence doc
        Note: For now we are retuning HTML information
        """
        await self.set_auth_handler()
        if not self.is_confluence_integration_enabled:
            return ""
        response = await self.__get_document()
        if response and response.get("body", {}).get("storage"):
            return ConfluenceHelper.parse_description(response["body"]["storage"]["value"])
        else:
            return ""

    async def __get_document(self) -> dict:
        """
        Extracts the Confluence document ID from the given Confluence link.

        Args:
        Returns:
            dict: returns confluence doc data
        """
        return await Page(auth_handler=self.auth_handler, client_account_id=self.client_account_id).get_document(
            self.document_id
        )
