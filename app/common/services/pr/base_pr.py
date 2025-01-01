from abc import ABC, abstractmethod

from app.common.services.credentials import AuthHandler
from app.common.services.repo.base_repo import BaseRepo
from app.common.utils.app_utils import get_token_count
from app.main.blueprints.deputy_dev.constants import PR_SIZING_TEXT, PR_SUMMARY_TEXT
from app.main.blueprints.deputy_dev.constants.repo import PR_NOT_FOUND
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.models.dto.pr.base_pr import BasePrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import (
    categorize_loc,
    files_to_exclude,
    format_summary_loc_time_text,
    ignore_files,
)


class BasePR(ABC):
    def __init__(
        self,
        vcs_type: str,
        workspace: str,
        repo_name: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        pr_id: str = None,
        repo_service: BaseRepo = None,
    ):
        self.vcs_type = vcs_type
        self.workspace = workspace
        self.pr_id = pr_id
        self.repo_name = repo_name
        self.pr_details: PullRequestResponse = None
        self.meta_data = f"repo: {repo_name}, pr_id: {pr_id}, user_name: {workspace}"
        self.comment_helper = None
        self.pr_json_data = None
        self.workspace_id = workspace_id
        self.pr_diff = None
        self.pr_stats = None
        self.auth_handler = auth_handler
        self.workspace_slug = workspace_slug
        self.pr_commit_diff = None
        self.repo_service = repo_service
        self.repo_client = None

    async def initialize(self):
        self.pr_details = await self.get_pr_details()
        if self.pr_details:
            self.branch_name = self.pr_details.branch_name
            self.repo_id = self.pr_details.scm_repo_id

    def get_pr_id(self):
        return self.pr_id

    @abstractmethod
    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        Raises:
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_pr_details(self, description):
        """
        Update details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Raises:
        """
        raise NotImplementedError()

    async def get_effective_pr_diff(self):
        """
        Determines whether to fetch the full PR diff or a specific commit diff.
        Returns:
            str: The appropriate diff based on context.
        """
        pr_reviewable_on_commit = get_context_value("pr_reviewable_on_commit")
        if pr_reviewable_on_commit:
            return await self.get_commit_diff()
        return await self.get_pr_diff()

    @abstractmethod
    async def get_pr_diff(self):
        """
        Get pr diff
        Args:
        Returns: str: PR diff
            An object containing details of the pull request.
        Raises:
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_commit_diff(self):
        """
        Get pr diff
        Args:
        Returns: str: PR diff
            An object containing details of the pull request.
        Raises:
        """
        raise NotImplementedError()

    def pr_json(self):
        return self.pr_json_data

    def pr_model(self) -> BasePrModel:
        pass

    async def get_pr_comments(self):
        """
        Get pr_comments.

        Returns:
            list: List of all comments for the pull request.
        """
        raise NotImplementedError()

    async def get_pr_stats(self) -> dict:
        """
        Returns PR stats

        Returns:
            dict:
            sample value {
                "total_added": "",
                "total_removed": "",
            }
        """
        raise NotImplementedError()

    async def get_loc_changed_count(self) -> int:
        raise NotImplementedError()

    async def get_pr_diff_token_count(self) -> int:
        pr_diff = await self.get_effective_pr_diff()
        if not pr_diff or pr_diff == PR_NOT_FOUND:
            return 0
        return get_token_count(pr_diff)

    async def generate_pr_description(self, pr_summary: str) -> str:
        """
        Generates a pull request (PR) description by combining an existing description
        (if available) with a provided summary and a calculated size category based
        on lines of code (LOC) changed.

        Args:
            pr_summary (str): A brief summary of the pull request to be included
                            in the description.

        Returns:
            dict: A string containing the updated PR description to be used in
                the update request.
        """
        loc = await self.get_loc_changed_count()
        category, time = categorize_loc(loc)
        loc_text, time_text = format_summary_loc_time_text(loc, category, time)

        if self.pr_details.description:
            description = f"{self.pr_details.description}\n\n---\n\n{PR_SIZING_TEXT.format(category=category, loc=loc_text, time=time_text)}\n\n---\n\n{PR_SUMMARY_TEXT}{pr_summary}"
        else:
            description = f"\n\n---\n\n{PR_SIZING_TEXT.format(category=category, loc=loc_text, time=time_text)}\n\n---\n\n{PR_SUMMARY_TEXT}{pr_summary}"
        # Prepare the data for the update request
        return description

    async def update_pr_description(self, pr_summary):
        try:
            description = await self.generate_pr_description(pr_summary)
            return await self.update_pr_details(description)
        except Exception as ex:
            AppLogger.log_error(f"PR description was not updated {ex}")

    async def create_pr(self, title, description, source_branch, destination_branch) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def get_pr_commits(self) -> list:
        """
        Get all commits in the PR with pagination support.

        Returns:
            list: List of commits in standardized format:
            [
                {
                    'hash': str,          # Commit hash
                    'parents': list,      # List of parent commits
                    'message': str,       # Commit message
                    'date': str,          # Commit date
                    'author': str         # Author information
                }
            ]
        """
        raise NotImplementedError()

    def exclude_pr_diff(self, pr_diff):
        settings = get_context_value("setting") or {}
        code_review_agent = settings.get("code_review_agent", {})
        inclusions = code_review_agent.get("inclusions", [])
        exclusions = code_review_agent.get("exclusions", [])
        excluded_files = files_to_exclude(exclusions, inclusions, "")
        return ignore_files(pr_diff, excluded_files)
