from sanic.log import logger
from torpedo.exceptions import BadRequestException

from app.common.service_clients.github.github_repo_client import GithubRepoClient
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.models.dto.pr.github_pr import GitHubPrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.utils import ignore_files


class GithubRepo(BaseRepo):
    def __init__(self, workspace: str, repo_name: str, pr_id: str, workspace_id: str):
        super().__init__(
            vcs_type=VCSTypes.bitbucket.value,
            workspace=workspace,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace_id=workspace_id,
        )
        self.repo_client = GithubRepoClient

    """
    Manages Github Repo
    """

    async def get_pr_diff(self):
        response = await self.repo_client.get_pr_diff(
            user_name=self.workspace, pr_id=self.pr_id, repo_name=self.repo_name
        )
        if response.status_code != 200:
            logger.error(f"unable to get pr diff {self.meta_data}")

        return ignore_files(response)

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
            response = await self.repo_client.get_pr_details(
                user_name=self.workspace,
                pr_id=self.pr_id,
                repo_name=self.repo_name,
            )
            if not response or response.status_code != 200:
                logger.error(f"unable to get pr details {self.meta_data}")
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
        return GitHubPrModel(pr_detail=self.pr_json(), meta_info={"scm_workspace_id": self.scm_workspace_id()})
