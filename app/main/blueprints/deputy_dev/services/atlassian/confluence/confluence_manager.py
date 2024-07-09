from app.common.service_clients.confluence.page import Page

from .confluence_helper import ConfluenceHelper


class ConfluenceManager:
    def __init__(self, document_id: str):
        self.document_id = document_id

    async def get_description_text(self):
        """
        Extracts the Confluence document ID from the given Confluence link.
        Returns:
            str: returns description of confluence doc
        Note: For now we are retuning HTML information
        """
        response = await self.get_document()
        if response and response.get("body", {}).get("storage"):
            return ConfluenceHelper.parse_description(response["body"]["storage"]["value"])
        else:
            return ""

    async def get_document(self) -> dict:
        """
        Extracts the Confluence document ID from the given Confluence link.

        Args:
        Returns:
            dict: returns confluence doc data
        """
        return await Page.get(self.document_id)
