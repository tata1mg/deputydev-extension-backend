import asyncio
import os
import re
import shutil
from abc import ABC
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple

import toml
from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo
from deputydev_core.utils.app_logger import AppLogger
from git.util import Actor
from sanic.log import logger

from app.backend_common.constants.constants import (
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
)
from app.backend_common.models.dao.postgres.repos import Repos
from app.backend_common.models.dao.postgres.workspaces import Workspaces
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.utils.sanic_wrapper import CONFIG


def parse_collection_name(name: str) -> str:
    # Replace any non-alphanumeric characters with hyphens
    name = re.sub(r"[^\w-]", "--", name)
    # Ensure the name is between 3 and 63 characters and starts/ends with alphanumeric
    name = re.sub(r"^(-*\w{0,61}\w)-*$", r"\1", name[:63].ljust(3, "x"))
    return name


class BaseRepo(ABC):
    def __init__(
        self,
        vcs_type: str,
        workspace: str,
        repo_name: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        repo_id: str | None = None,
    ) -> None:
        self.vcs_type = vcs_type
        self.workspace = workspace
        self.repo_name = repo_name
        self.workspace_id = workspace_id
        self.repo_id = repo_id
        self.auth_handler = auth_handler
        self.workspace_slug = workspace_slug
        self.repo_client = None

        # local repo
        self.local_repo = None

    def delete_local_repo(self) -> bool:
        """
        Remove the cloned repo
        """
        try:
            shutil.rmtree(self.repo_dir)
            return True
        except Exception:  # noqa: BLE001
            return False

    def apply_diff_on_local_repo(self, diff: Dict[str, List[Tuple[int, int, str]]]) -> None:
        """
        Apply the diff on the local repo
        """
        if not self.local_repo:
            raise ValueError("Local repo not initialized, please clone the repo first")
        self.local_repo.apply_diff(diff)

    def repo_full_name(self) -> str:
        return f"{self.workspace}/{self.repo_name}"

    @cached_property
    def repo_dir(self) -> str:
        """
        Get the directory of the repository.
        """
        if self.local_repo:
            return self.local_repo.repo_path
        raise ValueError("Local repo not initialized, please clone the repo first")

    async def get_default_branch(self) -> Optional[str]:
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

        stdout, _stderr = await process.communicate()

        if process.returncode == 0:
            for line in stdout.decode().splitlines():
                if line.strip().startswith("HEAD branch:"):
                    return line.split(":")[1].strip()

        logger.error(f"Issue in fetching default branch for {repo_url}")
        return None

    async def clone_branch(self, branch_name: str, repo_dir_prefix: str) -> Tuple[GitRepo, bool, str]:
        """
        This is a private method to clone the repository if it doesn't exist locally or pull updates if it does.
        """

        if not repo_dir_prefix:
            raise ValueError("Repo dir prefix is required to clone the repo")

        repo_dir = os.path.join(  # noqa: PTH118
            CONFIG.config.get("REPO_BASE_DIR"),
            repo_dir_prefix,
            self.repo_full_name(),
            parse_collection_name(branch_name),
        )
        repo_url = await self.get_repo_url()
        process = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--branch",
            branch_name,
            "--depth",  # This creates a shallow clone with a history truncated to only the latest commit
            "1",  # This is the value of --depth flag
            "--single-branch",
            "--no-tags",  # This prevents Git from downloading any tags from the remote repository
            repo_url,
            repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # get the outcome of cloning through stdout and stderr
        stdout, stderr = await process.communicate()
        # Get the return code
        return_code = process.returncode
        if return_code == 0:
            AppLogger.log_info("Cloning completed")
        else:
            error_message = stderr.decode().strip()
            if return_code == 128 and "Invalid credentials" in error_message:
                AppLogger.log_error(f"Git clone failed due to invalid credentials: {error_message}")
                raise PermissionError(f"Invalid credentials: {error_message}")

            if return_code != 128:
                AppLogger.log_error(f"Error while cloning - return code: {return_code}. Error: {error_message}")
                # we are raising runtime error for other status code, so that it can be retried from the SQS after sometime
                raise RuntimeError(f"Git clone failed: {error_message}")
            # we return False, if we were unable to clone repo
            AppLogger.log_error(f"Error while cloning - return code: {return_code}. Error: {error_message}")
            return None, False, None

        self.local_repo = GitRepo(repo_dir)
        return self.local_repo, True, repo_dir

    def scm_workspace_id(self) -> str:
        return self.workspace_id

    def vcs(self) -> str:
        return self.vcs_type

    def get_repo_url(self) -> str:
        raise NotImplementedError()

    def get_remote_url_without_token(self) -> str:
        raise NotImplementedError()

    async def create_issue_comment(self, issue_id: str, comment: str) -> None:
        raise NotImplementedError()

    async def notify_pr_creation(self, issue_id: str, pr_url: str) -> None:
        comment = f"✨ Created pull request: {pr_url}"
        await self.create_issue_comment(issue_id, comment)

    async def push_to_remote(self, branch_name: str) -> None:
        await self.local_repo.push_to_remote(
            branch_name=branch_name,
            remote_repo_url=await self.get_repo_url(),
        )

    async def is_pr_open_between_branches(
        self, source_branch: str, destination_branch: str
    ) -> Tuple[bool, Optional[str]]:
        raise NotImplementedError()

    def checkout_branch(self, branch_name: str) -> None:
        if not self.local_repo:
            raise ValueError("Local repo not initialized, please clone the repo first")
        self.local_repo.checkout_branch(branch_name)

    def stage_changes(self) -> None:
        if not self.local_repo:
            raise ValueError("Local repo not initialized, please clone the repo first")
        self.local_repo.stage_changes()

    def commit_changes(self, commit_message: str) -> None:
        if not self.local_repo:
            raise ValueError("Local repo not initialized, please clone the repo first")
        self.local_repo.commit_changes(commit_message, self.get_repo_actor())

    async def get_settings(self, branch_name: str) -> Tuple[Dict[str, Any], Dict[str, str] | str]:
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

    async def fetch_repo(self) -> Optional[Repos]:
        if self.repo_id:
            scm_workspace_id = self.workspace_id
            scm_repo_id = self.repo_id
            scm = self.vcs_type
            workspace = await Workspaces.get_or_none(scm_workspace_id=scm_workspace_id, scm=scm)
            repo = await Repos.get_or_none(workspace_id=workspace.id, scm_repo_id=scm_repo_id)
            return repo

    def get_repo_actor(self) -> Actor:
        raise NotImplementedError(
            "This method should be implemented in the child class to return the actor of the repo"
        )
