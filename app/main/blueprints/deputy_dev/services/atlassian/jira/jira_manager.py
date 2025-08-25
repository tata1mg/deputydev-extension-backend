from typing import Any, Dict, List, Optional

from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.service_clients.jira.issue import Issue
from app.main.blueprints.deputy_dev.utils import get_auth_handler

from .jira_helper import JiraHelper


class JiraManager:
    def __init__(self, issue_id: str) -> None:
        self.issue_id = issue_id
        self.auth_handler = None
        self.issue_details = None
        self.client_account_id = None
        self.is_jira_integrations_enabled = False

    async def set_auth_handler(self) -> None:
        if not self.client_account_id or not self.auth_handler:
            confluence_auth_handler, integration_info = await get_auth_handler(
                client="jira", team_id=get_context_value("team_id")
            )
            if confluence_auth_handler and integration_info:
                self.auth_handler = confluence_auth_handler
                self.client_account_id = integration_info["client_account_id"]
                self.is_jira_integrations_enabled = True

    async def get_description_text(self) -> str:
        response = await self.__get_issue_details(fields=["description"])
        if response.get("fields", {}).get("description"):
            return JiraHelper.parse_description(response.get("fields").get("description").get("content", []))
        else:
            return ""

    async def __get_issue_details(self, fields: List[str] | None = None) -> Dict[str, Any]:
        if self.issue_details:
            return self.issue_details
        await self.set_auth_handler()
        if not self.is_jira_integrations_enabled:
            return {}
        self.issue_details = await Issue(
            auth_handler=self.auth_handler, client_account_id=self.client_account_id
        ).get_issue_details(issue_id=self.issue_id, fields=fields)
        return self.issue_details

    async def comment_on_issue(self, comment: str) -> Optional[Dict[str, Any]]:
        if not self.is_jira_integrations_enabled:
            return {}
        self.issue_details = await Issue(
            auth_handler=self.auth_handler, client_account_id=self.client_account_id
        ).comment_on_issue(issue_id=self.issue_id, comment=comment)

    async def get_confluence_link_attached(self) -> Optional[str]:
        """
        extracts confluence links from jira description
        Args:
        Returns:
            links str: document id
        """
        jira_story = await self.__get_issue_details()
        if jira_story and jira_story.get("fields", {}).get("description"):
            document_id = JiraHelper.extract_confluence_id_from_description(jira_story)
            return document_id
