import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from functools import cached_property

import git
from sanic.log import logger
from torpedo import CONFIG

from app.common.utils.app_utils import get_token_count
from app.main.blueprints.deputy_dev.constants import PR_SIZING_TEXT, PR_SUMMARY_TEXT
from app.main.blueprints.deputy_dev.constants.repo import PR_NOT_FOUND, VCS_REPO_URL_MAP
from app.main.blueprints.deputy_dev.models.dto.pr.base_pr import BasePrModel
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.utils import categorize_loc, parse_collection_name


class BaseRepo(ABC):
    def __init__(self, vcs_type: str, workspace: str, repo_name: str, pr_id: str, workspace_id: str):
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

    async def initialize(self):
        self.pr_details = await self.get_pr_details()
        if self.pr_details:
            self.branch_name = self.pr_details.branch_name

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

    async def __clone(self) -> git.Repo:
        """
        This is a private method to clone the repository if it doesn't exist locally or pull updates if it does.
        """
        process = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--branch",
            self.get_branch_name(),
            "--depth",  # This creates a shallow clone with a history truncated to only the latest commit
            "1",  # This is the value of --depth flag
            "--single-branch",
            "--no-tags",  # This prevents Git from downloading any tags from the remote repository
            VCS_REPO_URL_MAP[self.vcs_type].format(repo_name=f"{self.workspace}/{self.repo_name}"),
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
    async def update_pr_details(self) -> PullRequestResponse:
        """
        Update details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        Raises:
        """
        raise NotImplementedError()

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

    async def get_pr_diff_token_count(self) -> int:
        pr_diff = await self.get_pr_diff()
        if not pr_diff or pr_diff == PR_NOT_FOUND:
            return 0
        return get_token_count(pr_diff)

    async def generate_pr_description(self, pr_summary: str) -> dict:
        """
        Generates a pull request (PR) description by combining an existing description
        (if available) with a provided summary and a calculated size category based
        on lines of code (LOC) changed.

        Args:
            pr_summary (str): A brief summary of the pull request to be included
                            in the description.

        Returns:
            dict: A dictionary containing the updated PR description to be used in
                the update request. The key is 'description' and the value is
                the concatenated description string.
        """
        loc = await self.get_loc_changed_count()
        category = categorize_loc(loc)
        if self.pr_details.description:
            description = f"{self.pr_details.description}\n\n---\n\n{PR_SIZING_TEXT.format(category=category, loc=loc)}\n\n---\n\n{PR_SUMMARY_TEXT}{pr_summary}"
        else:
            description = f"\n\n---\n\n{PR_SIZING_TEXT.format(category=category, loc=loc)}\n\n---\n\n{PR_SUMMARY_TEXT}{pr_summary}"
        # Prepare the data for the update request
        data = {"description": description}
        return data

    async def update_pr_description(self, pr_summary):
        description = await self.generate_pr_description(pr_summary)
        return await self.update_pr_details(description)
