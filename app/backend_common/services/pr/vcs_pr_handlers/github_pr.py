from typing import Dict, List

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value, set_context_values

from app.backend_common.constants.constants import LARGE_PR_DIFF, PR_NOT_FOUND, VCSTypes
from app.backend_common.models.dto.comment_dto import CommentDTO
from app.backend_common.models.dto.pr.github_pr import GitHubPrModel
from app.backend_common.service_clients.github.github_repo_client import (
    GithubRepoClient,
)
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.services.repo.github_repo import GithubRepo
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException


class GithubPR(BasePR):
    def __init__(
        self,
        workspace: str,
        repo_name: str,
        pr_id: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        repo_service: GithubRepo,
    ) -> None:
        super().__init__(
            vcs_type=VCSTypes.github.value,
            workspace=workspace,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_service=repo_service,
        )
        self.repo_client = GithubRepoClient(
            workspace_slug=workspace_slug,
            repo=repo_name,
            pr_id=int(pr_id) if pr_id else None,
            auth_handler=auth_handler,
        )
        self.token = ""  # Assuming I will get token here

    """
    Manages Github Repo
    """

    async def get_pr_diff(self) -> str | None:
        if self.pr_diff:
            return self.pr_diff

        response = await self.repo_client.get_pr_diff()
        if response and response.status_code == 406:
            return LARGE_PR_DIFF
        if response and response.status_code != 200:
            return PR_NOT_FOUND
        return response.text

    async def get_commit_diff(self) -> str | None:
        """
        Get the diff between two commits in GitHub.

        Args:
            base_commit (str): The first commit hash.
            destination_commit (str): The second commit hash.

        Returns:
            str: The diff between two commits.

        Raises:
            ValueError: If the repo diff cannot be retrieved.
        """

        response = await self.repo_client.get_commit_diff(
            self.pr_details.commit_id, get_context_value("last_reviewed_commit")
        )
        if response and response.status_code != 200:
            return PR_NOT_FOUND
        return response.text

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
                AppLogger.log_error(
                    f"unable to get pr details {self.meta_data} status code {response.status_code if response else 'unknown'} "
                )
                raise BadRequestException(f"unable to get pr details for {self.meta_data}")
            self.pr_json_data = await response.json()

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
            "destination_branch_commit": pr_model.destination_branch_commit(),
            "scm_repo_id": pr_model.scm_repo_id(),
        }
        self.branch_name = data["branch_name"]
        return PullRequestResponse(**data)

    def pr_model(self) -> GitHubPrModel:
        return GitHubPrModel(
            pr_detail=self.pr_json(),
            meta_info={"scm_workspace_id": self.workspace_id},
        )

    async def get_file_stats_from_pulls(self) -> List[Dict[str, int]] | None:
        """
        Get PR file statistics using the pulls API endpoint.
        """
        pr_diff_stats_response = await self.repo_client.get_pr_diff_stats()

        if pr_diff_stats_response:
            return await pr_diff_stats_response.json()

    async def get_file_stats_from_commits(
        self, current_commit: str, last_reviewed_commit: str
    ) -> List[Dict[str, int]] | None:
        """
        Get PR file statistics by comparing two commits.

        Args:
            current_commit (str): Current commit SHA
            last_reviewed_commit (str): Last reviewed commit SHA
        """
        diff_stats_response = await self.repo_client.get_commit_diff_stats(current_commit, last_reviewed_commit)
        diff_stats_response_json = await diff_stats_response.json()

        if diff_stats_response:
            return diff_stats_response_json.get("files", [])

    async def get_pr_stats(self) -> Dict[str, int]:
        if self.pr_stats:
            return self.pr_stats

        # Compute stats
        total_added, total_removed = 0, 0

        pr_reviewable_on_commit = get_context_value("pr_reviewable_on_commit")

        files_changed_data = (
            await self.get_file_stats_from_commits(self.pr_details.commit_id, get_context_value("last_reviewed_commit"))
            if pr_reviewable_on_commit
            else await self.get_file_stats_from_pulls()
        )

        if files_changed_data:
            for file_stat in files_changed_data:
                total_added += file_stat.get("additions", 0)
                total_removed += file_stat.get("deletions", 0)

        self.pr_stats = {
            "total_added": total_added,
            "total_removed": total_removed,
        }
        return self.pr_stats

    async def update_pr_details(self, description: str) -> None:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """
        payload = {"body": description}
        return await self.repo_client.update_pr_details(payload)

    async def get_loc_changed_count(self) -> int:
        stats = await self.get_pr_stats()
        if stats:
            return stats["total_added"] + stats["total_removed"]
        else:
            raise Exception("Pr stats data not present")

    async def get_pr_commits(self) -> list:
        """Get all commits in the PR"""

        commits = await self.repo_client.get_pr_commits()

        # Format commits to standard structure
        formatted_commits = []
        for commit in commits:
            formatted_commits.append(
                {
                    "hash": commit.get("sha"),
                    "parents": commit.get("parents", []),
                    "message": commit.get("commit", {}).get("message"),
                    "date": commit.get("commit", {}).get("author", {}).get("date"),
                    "author": commit.get("commit", {}).get("author", {}).get("name"),
                }
            )

        return formatted_commits

    async def create_pr(self, title: str, description: str, source_branch: str, destination_branch: str) -> str | None:
        payload = {
            "title": title,
            "head": source_branch,
            "base": destination_branch,
            "body": description,
        }
        response = await self.repo_client.create_pr(payload)
        set_context_values(pr_url=response.get("html_url"))
        return response.get("html_url")

    async def get_pr_comments(self) -> List[CommentDTO]:
        pr_comments = await self.repo_client.get_pr_comments()
        formatted_pr_comments = []
        for pr_comment in pr_comments:
            comment = CommentDTO(scm_comment_id=str(pr_comment["id"]), body=pr_comment["body"])
            formatted_pr_comments.append(comment)
        return formatted_pr_comments
