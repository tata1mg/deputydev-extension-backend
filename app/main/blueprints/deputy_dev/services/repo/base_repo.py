import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from functools import cached_property

import git
import toml
from sanic.log import logger
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants import PR_SIZING_TEXT, PR_SUMMARY_TEXT
from app.main.blueprints.deputy_dev.constants.constants import (
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
)
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.models.dao import Repos, Workspaces
from app.main.blueprints.deputy_dev.models.dto.pr.base_pr import BasePrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler
from app.main.blueprints.deputy_dev.services.pr_diff_service import PRDiffService
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import (
    categorize_loc,
    format_summary_loc_time_text,
    parse_collection_name,
)


class BaseRepo(ABC):
    def __init__(
        self,
        vcs_type: str,
        workspace: str,
        repo_name: str,
        pr_id: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        repo_id: str = None,
    ):
        self.vcs_type = vcs_type
        self.workspace = workspace
        self.pr_id = pr_id
        self.repo_name = repo_name
        self.pr_details: PullRequestResponse = None
        self.branch_name = None
        self.meta_data = f"repo: {repo_name}, pr_id: {pr_id}, user_name: {workspace}"
        self.comment_helper = None
        self.pr_json_data = None
        self.workspace_id = workspace_id
        self.pr_diff = None
        self.pr_stats = None
        self.repo_id = repo_id
        self.auth_handler = auth_handler
        self.workspace_slug = workspace_slug
        self.pr_commit_diff = None
        self.repo_client = None
        self.pr_diff_service: PRDiffService = None

    async def initialize(self):
        self.pr_details = await self.get_pr_details()
        if self.pr_details:
            self.branch_name = self.pr_details.branch_name
            self.repo_id = self.pr_details.scm_repo_id

    def delete_repo(self) -> bool:
        """
        Remove the cloned repo
        """
        try:
            shutil.rmtree(self.repo_dir)
            return True
        except Exception:
            return False

    def repo_full_name(self):
        return f"{self.workspace}/{self.repo_name}"

    @cached_property
    def repo_dir(self) -> str:
        """
        Get the directory of the repository.
        """
        return os.path.join(
            CONFIG.config.get("REPO_BASE_DIR"),
            self.repo_full_name(),
            parse_collection_name(self.branch_name),
        )

    async def get_default_branch(self):
        """
        Response of 'git remote show https://github.com/tata1mg/hector' command:
          remote https://github.com/tata1mg/hector
          Fetch URL: https://github.com/tata1mg/hector
          Push  URL: https://github.com/tata1mg/hector
          HEAD branch: main
        """
        repo_url = await self.get_repo_url()
        process = await asyncio.create_subprocess_exec(
            "git", "remote", "show", repo_url, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            for line in stdout.decode().splitlines():
                if line.strip().startswith("HEAD branch:"):
                    return line.split(":")[1].strip()

        logger.error(f"Issue in fetching default branch for {repo_url}")
        return None

    async def __clone(self) -> git.Repo:
        """
        This is a private method to clone the repository if it doesn't exist locally or pull updates if it does.
        """
        repo_url = await self.get_repo_url()
        process = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--branch",
            self.get_branch_name(),
            "--depth",  # This creates a shallow clone with a history truncated to only the latest commit
            "1",  # This is the value of --depth flag
            "--single-branch",
            "--no-tags",  # This prevents Git from downloading any tags from the remote repository
            repo_url,
            self.repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # get the outcome of cloning through stdout and stderr
        stdout, stderr = await process.communicate()
        # Get the return code
        return_code = process.returncode
        if return_code == 0:
            logger.info("Cloning completed")
        else:
            error_message = stderr.decode().strip()
            if return_code == 128 and "Invalid credentials" in error_message:
                logger.error(f"Git clone failed due to invalid credentials: {error_message}")
                raise PermissionError(f"Invalid credentials: {error_message}")

            if return_code != 128:
                logger.error(f"Error while cloning - return code: {return_code}. Error: {error_message}")
                # we are raising runtime error for other status code, so that it can be retried from the SQS after sometime
                raise RuntimeError(f"Git clone failed: {error_message}")
            # we return False, if we were unable to clone repo
            return None, False

        repo = git.Repo(self.repo_dir)
        return repo, True

    async def clone_repo(self):
        """
        Initialize the repository after dataclass initialization.
        """
        return await self.__clone()

    def get_branch_name(self) -> str:
        return self.branch_name

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

    def scm_workspace_id(self) -> str:
        return self.workspace_id

    def vcs(self):
        return self.vcs_type

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

    def get_repo_url(self):
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
