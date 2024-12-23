from sanic.log import logger

from app.main.blueprints.deputy_dev.services.credentials import AuthHandler

from .base import Base


class Page(Base):
    ISSUE_PATH = "content"

    def __init__(self, auth_handler: AuthHandler, client_account_id):
        super().__init__(auth_handler)
        self.client_account_id = client_account_id

    async def get_document(self, document_id):
        if document_id:
            url = f"{self.BASE_URL}/{self.client_account_id}/{self.PATH}/{self.ISSUE_PATH}/{document_id}"
            query_params = {"expand": "body.storage,body.view"}
            try:
                response = await self.get(url, params=query_params)
                confluence_doc_data = await response.json()
                logger.info(f"Confluence issue details {confluence_doc_data}")
                return confluence_doc_data
            except Exception as e:
                logger.error("Exception occured while fetching issue details from jira: {}".format(e))
                return {}
        else:
            return {}
