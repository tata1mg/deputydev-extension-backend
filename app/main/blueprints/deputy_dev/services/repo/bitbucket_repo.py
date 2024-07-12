import re
from datetime import datetime

from app.common.service_clients.bitbucket.bitbucket_repo_client import (
    BitbucketRepoClient,
)
from app.main.blueprints.deputy_dev.constants.jira import (
    ATLASSIAN_ISSUE_URL_PREFIX,
    ISSUE_ID_REGEX,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.utils import ignore_files


class BitbucketRepo(BaseRepo):
    def __init__(self, workspace: str, repo_name: str, pr_id: str):
        super().__init__(vcs_type=VCSTypes.bitbucket.value, workspace=workspace, repo_name=repo_name, pr_id=pr_id)
        self.repo_client = BitbucketRepoClient(workspace=workspace, repo=repo_name, pr_id=int(pr_id))

    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """

        pr_details = await self.repo_client.get_pr_details()
        if pr_details:
            data = pr_details
            data["issue_id"] = self.__get_issue_id(data.get("rendered", {}).get("title", {}))
            data["created_on"] = datetime.fromisoformat(data["created_on"])
            data["updated_on"] = datetime.fromisoformat(data["updated_on"])
            data["branch_name"] = data["source"]["branch"]["name"]
            return PullRequestResponse(**data)

    async def get_pr_diff(self):
        """
        Get PR diff of a pull request from Bitbucket, Github or Gitlab.

        Args:
        Returns:
            str: The diff of a pull request

        Raises:
            ValueError: If the pull request diff cannot be retrieved.
        """

        pr_diff = await self.repo_client.get_pr_diff()
        if pr_diff:
            return ignore_files(pr_diff)

    def __get_issue_id(self, title) -> str:
        title_html = title.get("html", "")
        if title_html:
            escaped_prefix = re.escape(ATLASSIAN_ISSUE_URL_PREFIX) + ISSUE_ID_REGEX
            matched_text = re.search(escaped_prefix, title_html)
            if matched_text is not None:
                issue_url = matched_text.group()
                return issue_url.replace(ATLASSIAN_ISSUE_URL_PREFIX, "")
