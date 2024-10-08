from sanic.log import logger
from torpedo.exceptions import BadRequestException

from app.common.service_clients.github.github_repo_client import GithubRepoClient
from app.main.blueprints.deputy_dev.constants.repo import (
    PR_NOT_FOUND,
    VCS_REPO_URL_MAP,
    VCSTypes,
)
from app.main.blueprints.deputy_dev.models.dto.pr.github_pr import GitHubPrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.utils import ignore_files


class GithubRepo(BaseRepo):
    def __init__(
        self,
        workspace: str,
        repo_name: str,
        pr_id: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        repo_id: str = None,
    ):
        super().__init__(
            vcs_type=VCSTypes.github.value,
            workspace=workspace,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )
        self.repo_client = GithubRepoClient(
            workspace_slug=workspace_slug, repo=repo_name, pr_id=int(pr_id), auth_handler=auth_handler
        )
        self.token = ""  # Assuming I will get token here

    """
    Manages Github Repo
    """

    async def get_pr_diff(self):
        if self.pr_diff:
            return self.pr_diff

        response = await self.repo_client.get_pr_diff()
        if response.status_code != 200:
            return PR_NOT_FOUND
        self.pr_diff = ignore_files(response.text)
        return self.pr_diff

    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        if not self.pr_json_data:
            response = await self.repo_client.get_pr_details()
            if not response or response.status_code != 200:
                logger.error(f"unable to get pr details {self.meta_data} status code {response.status_code} ")
                raise BadRequestException(f"unable to get pr details for {self.meta_data}")
            self.pr_json_data = response.json()

        pr_model = GitHubPrModel(self.pr_json_data)
        data = {
            "id": pr_model.scm_pr_id(),
            "state": pr_model.scm_state(),
            "title": pr_model.title(),
            "description": pr_model.description(),
            "created_on": pr_model.scm_creation_time(),
            "updated_on": pr_model.scm_updation_time(),
            "branch_name": pr_model.source_branch(),
            "commit_id": pr_model.commit_id(),
        }
        self.branch_name = data["branch_name"]
        return PullRequestResponse(**data)

    def pr_model(self):
        return GitHubPrModel(
            pr_detail=self.pr_json(),
            meta_info={"scm_workspace_id": self.scm_workspace_id()},
        )

    async def get_pr_stats(self):
        if self.pr_stats:
            return self.pr_stats

        # Compute stats
        total_added, total_removed = 0, 0
        pr_diff_stats_response = await self.repo_client.get_pr_diff_stats()
        if pr_diff_stats_response:
            files_changed_data = pr_diff_stats_response.json()
            if files_changed_data:
                for file_stat in files_changed_data:
                    total_added += file_stat.get("additions", 0)
                    total_removed += file_stat.get("deletions", 0)

        self.pr_stats = {
            "total_added": total_added,
            "total_removed": total_removed,
        }
        return self.pr_stats

    async def update_pr_details(self, description) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """
        payload = {"body": description}
        self.pr_json_data = await self.repo_client.update_pr_details(payload)

    async def get_loc_changed_count(self):
        stats = await self.get_pr_stats()
        if stats:
            return stats["total_added"] + stats["total_removed"]
        else:
            raise Exception("Pr stats data not present")

    async def get_repo_url(self):
        self.token = await self.auth_handler.access_token()
        return VCS_REPO_URL_MAP[self.vcs_type].format(
            token=self.token, workspace_slug=self.workspace_slug, repo_name=self.repo_name
        )
