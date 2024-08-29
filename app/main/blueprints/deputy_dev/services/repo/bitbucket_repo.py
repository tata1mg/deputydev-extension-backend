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

    def parse_pr_detail_response(self, pr_model: BitbucketPrModel) -> PullRequestResponse:
        """
        Parses the details of a pull request and returns a PullRequestResponse object.

        Args:
            pr_model (object): An object representing the pull request model, containing details about the PR.

        Returns:
            PullRequestResponse: An instance of PullRequestResponse containing the parsed pull request data.

        Parsed Data:
            - id (str): The ID of the pull request.
            - state (str): The state of the pull request (e.g., open, closed).
            - issue_id (str): The ID of the associated issue, if any.
            - created_on (datetime): The creation time of the pull request.
            - updated_on (datetime): The last update time of the pull request.
            - branch_name (str): The name of the source branch of the pull request.
            - title (str): The title of the pull request.
            - description (str): The description of the pull request.
            - commit_id (str): The ID of the commit associated with the pull request.
        """
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
            return self.parse_pr_detail_response(pr_model)

    async def update_pr_details(self, payload) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """
        self.pr_json_data = await self.repo_client.update_pr_details(payload)
        pr_model = BitbucketPrModel(self.pr_json_data)
        if self.pr_json_data:
            return self.parse_pr_detail_response(pr_model)

    async def get_pr_comments(self):
        comments = await self.repo_client.get_pr_comments()
        return comments

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

    async def get_pr_stats(self):
        if self.pr_stats:
            return self.pr_stats
        # compute stats
        total_added, total_removed = (0, 0)
        pr_diff_stats_response = await self.repo_client.get_pr_diff_stats()
        if pr_diff_stats_response:
            files_changed_data = pr_diff_stats_response.json()
            if files_changed_data and files_changed_data.get("values"):
                files_changed_data = files_changed_data["values"]
                total_added = 0
                total_removed = 0
                for file_stat in files_changed_data:
                    total_added += file_stat["lines_added"]
                    total_removed += file_stat["lines_removed"]
        self.pr_stats = {
            "total_added": total_added,
            "total_removed": total_removed,
        }
        return self.pr_stats

    async def get_loc_changed_count(self):
        stats = await self.get_pr_stats()
        if stats:
            return stats["total_added"] + stats["total_removed"]
        else:
            raise Exception("Pr stats data not present")
