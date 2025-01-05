from abc import ABC, abstractmethod

import toml
from torpedo import CONFIG

from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.utils.formatting import (
    PRDiffSizingLabel,
    format_summary_loc_time_text,
)
from app.common.constants.constants import PR_SIZING_TEXT, PR_SUMMARY_TEXT
from app.common.utils.app_logger import AppLogger
from app.common.utils.context_vars import get_context_value
from app.main.blueprints.deputy_dev.constants.constants import (
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
)
from app.main.blueprints.deputy_dev.models.dao.postgres import Repos, Workspaces
from app.main.blueprints.deputy_dev.services.pr_diff_service import PRDiffService


def categorize_loc(loc: int) -> tuple:
    """
    Categorizes the number of lines of code (LOC) into predefined size categories.

    Args:
        loc (int): The total number of lines of code.

    Returns:
        str: The size category based on the number of lines of code.
            - "XS" for 0-9 lines
            - "S" for 10-29 lines
            - "M" for 30-99 lines
            - "L" for 100-499 lines
            - "XL" for 500-999 lines
            - "XXL" for 1000+ lines
    """
    if loc < 10:
        return PRDiffSizingLabel.XS.value, PRDiffSizingLabel.XS_TIME.value
    elif loc < 30:
        return PRDiffSizingLabel.S.value, PRDiffSizingLabel.S_TIME.value
    elif loc < 100:
        return PRDiffSizingLabel.M.value, PRDiffSizingLabel.M_TIME.value
    elif loc < 500:
        return PRDiffSizingLabel.L.value, PRDiffSizingLabel.L_TIME.value
    elif loc < 1000:
        return PRDiffSizingLabel.XL.value, PRDiffSizingLabel.XL_TIME.value
    else:
        return PRDiffSizingLabel.XXL.value, PRDiffSizingLabel.XXL_TIME.value


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
        self.pr_diff_service: PRDiffService = None

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

    async def get_effective_pr_diff(self, operation="code_review", agent_id=None):
        # TODO: Document this function
        """
        Determines whether to fetch the full PR diff or a specific commit diff.
        Returns:
            str: The appropriate diff based on context.
        """
        await self.initialize_pr_diff_service()
        return self.pr_diff_service.get_pr_diff(operation, agent_id)

    async def initialize_pr_diff_service(self):
        if not self.pr_diff_service:
            pr_reviewable_on_commit = get_context_value("pr_reviewable_on_commit")
            if pr_reviewable_on_commit:
                pr_diff = await self.get_commit_diff()
                pr_diff = pr_diff.json
            else:
                pr_diff = await self.get_pr_diff()
            self.pr_diff_service = PRDiffService(pr_diff)

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

    async def get_pr_diff_token_count(self, operation="code_review") -> int:
        #  This function is called from two places
        #  first time insertion of pr while code review
        #  second time when pr is large
        await self.initialize_pr_diff_service()
        return self.pr_diff_service.pr_diffs_token_counts_agent_name_wise(operation)

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

    async def get_settings(self, branch_name):
        settings = await self.repo_client.get_file(branch_name, CONFIG.config["REPO_SETTINGS_FILE"])
        if settings:
            try:
                settings = toml.loads(settings.text)
                return settings, {}
            except toml.TomlDecodeError as e:
                error_type = SettingErrorType.INVALID_TOML.value
                error = {error_type: f"""{SETTING_ERROR_MESSAGE[error_type]}{str(e)}"""}
                return {}, error
        else:
            return {}, {}

    async def fetch_repo(self):
        if self.repo_id:
            scm_workspace_id = self.workspace_id
            scm_repo_id = self.repo_id
            scm = self.vcs_type
            workspace = await Workspaces.get_or_none(scm_workspace_id=scm_workspace_id, scm=scm)
            repo = await Repos.get_or_none(workspace_id=workspace.id, scm_repo_id=scm_repo_id)
            return repo
