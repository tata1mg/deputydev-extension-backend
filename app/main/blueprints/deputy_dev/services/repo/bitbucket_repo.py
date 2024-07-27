import re

from app.common.service_clients.bitbucket.bitbucket_repo_client import (
    BitbucketRepoClient,
)
from app.main.blueprints.deputy_dev.constants.jira import (
    ATLASSIAN_ISSUE_URL_PREFIX,
    ISSUE_ID_REGEX,
)
from app.main.blueprints.deputy_dev.constants.repo import PR_NOT_FOUND, VCSTypes
from app.main.blueprints.deputy_dev.models.dto.pr.bitbucket_pr import BitbucketPrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.utils import ignore_files


class BitbucketRepo(BaseRepo):
    def __init__(self, workspace: str, repo_name: str, pr_id: str, workspace_id: str):
        super().__init__(
            vcs_type=VCSTypes.bitbucket.value,
            workspace=workspace,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace_id=workspace_id,
        )
        self.repo_client = BitbucketRepoClient(workspace=workspace, repo=repo_name, pr_id=int(pr_id))

    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """
        self.pr_json_data = await self.repo_client.get_pr_details()
        pr_model = BitbucketPrModel(self.pr_json_data)
        if self.pr_json_data:
            data = {
                "id": pr_model.scm_pr_id(),
                "state": pr_model.scm_state(),
                "issue_id": self.__get_issue_id(self.pr_json_data.get("rendered", {}).get("title", {})),
                "created_on": pr_model.scm_creation_time(),
                "updated_on": pr_model.scm_updation_time(),
                "branch_name": pr_model.source_branch(),
                "title": pr_model.title(),
                "description": pr_model.description(),
                "commit_id": pr_model.commit_id(),
            }
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
        if self.pr_diff:
            return self.pr_diff

        pr_diff, status_code = await self.repo_client.get_pr_diff()
        if status_code == 404:
            return PR_NOT_FOUND

        if pr_diff:
            self.pr_diff = ignore_files(pr_diff)
        return self.pr_diff

    def __get_issue_id(self, title) -> str:
        title_html = title.get("html", "")
        if title_html:
            escaped_prefix = re.escape(ATLASSIAN_ISSUE_URL_PREFIX) + ISSUE_ID_REGEX
            matched_text = re.search(escaped_prefix, title_html)
            if matched_text is not None:
                issue_url = matched_text.group()
                return issue_url.replace(ATLASSIAN_ISSUE_URL_PREFIX, "")

    def pr_model(self):
        return BitbucketPrModel(pr_detail=self.pr_json(), meta_info={"scm_workspace_id": self.scm_workspace_id()})
