import re
from typing import List

from deputydev_core.utils.context_vars import get_context_value, set_context_values

from app.backend_common.constants.constants import PR_NOT_FOUND, VCSTypes
from app.backend_common.models.dto.comment_dto import CommentDTO
from app.backend_common.models.dto.pr.bitbucket_pr import BitbucketPrModel
from app.backend_common.service_clients.bitbucket import BitbucketRepoClient
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.services.repo.bitbucket_repo import BitbucketRepo

ATLASSIAN_ISSUE_URL_PREFIX = "https://1mgtech.atlassian.net/browse/"
ISSUE_ID_REGEX = r"[A-Z]+-\d+"


class BitbucketPR(BasePR):
    def __init__(
        self,
        workspace: str,
        repo_name: str,
        pr_id: str,
        workspace_id: str,
        auth_handler: AuthHandler,
        workspace_slug: str,
        repo_service: BitbucketRepo,
    ):
        super().__init__(
            vcs_type=VCSTypes.bitbucket.value,
            workspace=workspace,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_service=repo_service,
        )
        self.repo_client = BitbucketRepoClient(
            workspace_slug=workspace_slug,
            repo=repo_name,
            pr_id=int(pr_id) if pr_id else None,
            auth_handler=auth_handler,
        )
        self.token = ""

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
            "destination_branch_commit": pr_model.destination_branch_commit(),
            "scm_repo_id": pr_model.scm_repo_id(),
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

    async def update_pr_details(self, description):
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        """
        payload = {"description": description}
        await self.repo_client.update_pr_details(payload)

    async def get_pr_diff(self):
        """
        Get PR diff of a pull request from Bitbucket, Github or Gitlab.

        Args:
        Returns:
            str: The diff of a pull request

        Raises:
            ValueError: If the pull request diff cannot be retrieved.
        """
        pr_diff, status_code = await self.repo_client.get_pr_diff()
        if status_code == 404:
            return PR_NOT_FOUND
        return pr_diff.text

    async def get_commit_diff(self):
        """
        Get the diff between two commits in Bitbucket.

        Args:
            base_commit (str): The first commit hash.
            destination_commit (str): The second commit hash.

        Returns:
            str: The diff between two commits.

        Raises:
            ValueError: If the repo diff cannot be retrieved.
        """

        commit_diff, status_code = await self.repo_client.get_commit_diff(
            self.pr_details.commit_id, get_context_value("last_reviewed_commit")
        )
        if status_code == 404:
            return PR_NOT_FOUND
        return commit_diff.text if commit_diff else ""

    def __get_issue_id(self, title) -> str:
        title_html = title.get("html", "")
        if title_html:
            escaped_prefix = re.escape(ATLASSIAN_ISSUE_URL_PREFIX) + ISSUE_ID_REGEX
            matched_text = re.search(escaped_prefix, title_html)
            if matched_text is not None:
                issue_url = matched_text.group()
                return issue_url.replace(ATLASSIAN_ISSUE_URL_PREFIX, "")

    def pr_model(self):
        return BitbucketPrModel(
            pr_detail=self.pr_json(),
            meta_info={"scm_workspace_id": self.workspace_id},
        )

    async def get_pr_stats(self):
        if self.pr_stats:
            return self.pr_stats
        # compute stats
        total_added, total_removed = (0, 0)
        pr_reviewable_on_commit = get_context_value("pr_reviewable_on_commit")

        pr_diff_stats_response = (
            await self.repo_client.get_commit_diff_stats(
                self.pr_details.commit_id, get_context_value("last_reviewed_commit")
            )
            if pr_reviewable_on_commit
            else await self.repo_client.get_pr_diff_stats()
        )

        if pr_diff_stats_response:
            files_changed_data = await pr_diff_stats_response.json()
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

    async def create_pr(self, title, description, source_branch, destination_branch):
        payload = {
            "title": title,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": destination_branch}},
            "description": description,
        }
        response = await self.repo_client.create_pr(payload)
        if response.get("type") == "error":
            raise ValueError(response.get("error", {}).get("message"))

        set_context_values(pr_url=response.get("links", {}).get("html", {}).get("href"))
        return response.get("links", {}).get("html", {}).get("href")

    async def get_pr_commits(self) -> list:
        """Get all commits in the PR"""

        commits = await self.repo_client.get_pr_commits()

        # Format commits to standard structure
        formatted_commits = []
        for commit in commits:
            formatted_commits.append(
                {
                    "hash": commit.get("hash"),
                    "parents": commit.get("parents", []),
                    "message": commit.get("message"),
                    "date": commit.get("date"),
                    "author": commit.get("author", {}).get("raw"),
                }
            )

        return formatted_commits

    async def get_pr_comments(self) -> List[CommentDTO]:
        pr_comments = await self.repo_client.get_pr_comments()
        formatted_pr_comments = []
        for pr_comment in pr_comments:
            comment = CommentDTO(scm_comment_id=str(pr_comment["id"]), body=pr_comment["content"]["raw"])
            formatted_pr_comments.append(comment)
        return formatted_pr_comments
