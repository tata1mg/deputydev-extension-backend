from sanic.log import logger
from torpedo.exceptions import BadRequestException

from app.common.service_clients.gitlab.gitlab_repo_client import GitlabRepoClient
from app.main.blueprints.deputy_dev.constants.repo import (
    PR_NOT_FOUND,
    VCS_REPO_URL_MAP,
    VCSTypes,
)
from app.main.blueprints.deputy_dev.models.dto.pr.gitlab_pr import GitlabPrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.utils import ignore_files


class GitlabRepo(BaseRepo):
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
            vcs_type=VCSTypes.gitlab.value,
            workspace=workspace,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )
        self.repo_client = GitlabRepoClient(pr_id=pr_id, project_id=self.repo_id, auth_handler=auth_handler)

    def parse_pr_detail_response(self, pr_model: GitlabPrModel) -> PullRequestResponse:
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
            "title": pr_model.title(),
            "description": pr_model.description(),
            "created_on": pr_model.scm_creation_time(),
            "updated_on": pr_model.scm_updation_time(),
            "branch_name": pr_model.source_branch(),
            "commit_id": pr_model.commit_id(),
            "diff_refs": pr_model.diff_refs(),
        }
        return PullRequestResponse(**data)

    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """
        if not self.pr_json_data:
            self.pr_json_data = await self.repo_client.get_pr_details()
            if not self.pr_json_data:
                logger.error(f"unable to get pr details {self.meta_data}")
                raise BadRequestException(f"unable to get pr details for {self.meta_data}")

        self.pr_json_data["repo_name"] = self.repo_name
        pr_model = GitlabPrModel(self.pr_json_data)
        if self.pr_json_data:
            return self.parse_pr_detail_response(pr_model)

    async def update_pr_details(self, description):
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
        """
        payload = {"description": description}
        return await self.repo_client.update_pr_details(payload)

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

        response, status_code = await self.repo_client.get_pr_diff()
        if status_code == 404:
            return PR_NOT_FOUND

        if response:
            combined_pr_diff = self.create_combined_diff_text(response["changes"])
            self.pr_diff = ignore_files(combined_pr_diff)
        return self.pr_diff

    @staticmethod
    def create_combined_diff_text(changes):
        combined_diff = ""

        for change in changes:
            old_file = change["old_path"]
            new_file = change["new_path"]
            diff_content = change["diff"]

            # File headers similar to a standard diff format
            file_header = f"diff --git a/{old_file} b/{new_file}\n"
            file_mode_header = f"--- a/{old_file}\n+++ b/{new_file}\n"

            # Combine headers and diff content
            combined_diff += file_header + file_mode_header + diff_content + "\n"

        return combined_diff

    def pr_model(self):
        return GitlabPrModel(pr_detail=self.pr_json(), meta_info={"scm_workspace_id": self.scm_workspace_id()})

    async def get_pr_stats(self):
        if self.pr_stats:
            return self.pr_stats

        total_added, total_removed = (0, 0)
        pr_diff = await self.get_pr_diff()
        diff_lines = pr_diff.split("\n")

        if diff_lines:
            for line in diff_lines:
                if line.startswith("+") and not line.startswith("+++"):
                    total_added += 1

                elif line.startswith("-") and not line.startswith("---"):
                    total_removed += 1

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

    def get_repo_url(self):
        return VCS_REPO_URL_MAP[self.vcs_type].format(
            token=self.token, workspace_slug=self.workspace_slug, repo_name=self.repo_name
        )
