from typing import Optional

from app.common.service_clients.jira.issue import Issue

from .jira_helper import JiraHelper


class JiraManager:
    def __init__(self, issue_id: str):
        self.issue_id = issue_id
        self.issue_details = None

    async def get_description_text(self):
        response = await self.get_issue_details(fields=["description"])
        if response.get("fields", {}).get("description"):
            return JiraHelper.parse_description(response.get("fields").get("description").get("content", []))
        else:
            return ""

    async def get_issue_details(self, fields: list[str] = None):
        if self.issue_details:
            return self.issue_details
        self.issue_details = await Issue.get(self.issue_id, fields)
        return self.issue_details

    async def get_confluence_link_attached(self) -> Optional[str]:
        """
        extracts confluence links from jira description
        Args:
        Returns:
            links str: document id
        """
        jira_story = await self.get_issue_details()
        if not jira_story:
            return
        document_id = JiraHelper.extract_confluence_id_from_description(jira_story)
        return document_id
