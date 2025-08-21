from typing import Any, Dict

from sanic.log import logger

from app.backend_common.services.credentials import AuthHandler

from .base import Base


class Issue(Base):
    def __init__(self, auth_handler: AuthHandler, client_account_id: str) -> None:
        super().__init__(auth_handler)
        self.client_account_id = client_account_id

    ISSUE_PATH = "issue"

    async def get_issue_details(self, issue_id: int, fields: str | None = None) -> Dict[str, Any]:
        # returns no response if issue_id is not present
        if not issue_id:
            return {}

        url = f"{self.BASE_URL}/{self.client_account_id}/{self.V3_PATH}/{self.ISSUE_PATH}/{issue_id}"
        query_params = {}
        if fields:
            query_params["fields"] = fields
        try:
            response = await self.get(url, params=query_params)
            issue_details = await response.json()
            logger.info(f"Jira issue details {issue_details}")
            return issue_details
        except Exception as e:  # noqa: BLE001
            logger.error("Exception occurred while fetching issue details from jira: {}".format(e))
        return {}

    async def comment_on_issue(self, issue_id: str, comment: str) -> Dict[str, Any] | None:
        if not issue_id:
            return
        url = f"{self.BASE_URL}/{self.client_account_id}/{self.V3_PATH}/{self.ISSUE_PATH}/{issue_id}/comment"
        data = {
            "body": {
                "content": [
                    {
                        "content": [
                            {
                                "text": comment,
                                "type": "text",
                            }
                        ],
                        "type": "paragraph",
                    }
                ],
                "type": "doc",
                "version": 1,
            }
        }
        try:
            response = await self.post(url, json=data)
            return response.json()
        except Exception as e:  # noqa: BLE001
            logger.error("Exception occurred while fetching issue details from jira: {}".format(e))
        return {}
