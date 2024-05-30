from app.service_clients.jira.issue import Issue

from .jira_helper import JiraHelper


class JiraManager:
    def __init__(self, issue_id: str):
        self.issue_id = issue_id

    async def get_description_text(self):
        response = await self.get_issue_details(fields=["description"])
        return JiraHelper.parse_description(response.get("fields", {}).get("description", {}).get("content", {}))

    async def get_issue_details(self, fields: list[str]):
        return await Issue.get(self.issue_id, fields)
