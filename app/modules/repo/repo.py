import os
import re
import shutil
from functools import cached_property
from typing import Union

import git
from sanic.log import logger
from torpedo import CONFIG

from app.constants import RepoUrl
from app.constants.repo import VCSTypes
from app.utils import add_corrective_code, parse_collection_name

from .bitbucket import BitBucketModule


class RepoModule:
    """Represents a module for handling repositories."""

    def __init__(self, repo_full_name: str, branch_name: str, vcs_type: VCSTypes) -> None:
        self.repo_full_name = repo_full_name
        self.branch_name = branch_name
        self.vcs_type = vcs_type

    def delete_repo(self) -> bool:
        """
        Remove the cloned repo
        """
        try:
            shutil.rmtree(self.repo_dir)
            return True
        except Exception:
            return False

    @cached_property
    def repo_dir(self) -> str:
        """
        Get the directory of the repository.
        """
        return os.path.join(
            CONFIG.config.get("REPO_BASE_DIR"),
            self.repo_full_name,
            parse_collection_name(self.branch_name),
        )

    def __clone(self) -> git.Repo:
        """
        This is a private method to clone the repository if it doesn't exist locally or pull updates if it does.
        """

        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")

        if not os.path.exists(self.repo_dir):
            logger.info("Cloning repo...")
            if self.branch_name:
                repo = git.Repo.clone_from(
                    RepoUrl.BITBUCKET_URL.value.format(repo_name=self.repo_full_name),
                    self.repo_dir,
                    branch=self.branch_name,
                )
            else:
                repo = git.Repo.clone_from(
                    RepoUrl.BITBUCKET_URL.value.format(repo_name=self.repo_full_name), self.repo_dir
                )
            logger.info("Done cloning")
        else:
            try:
                repo = git.Repo(self.repo_dir)
                repo.remotes.origin.pull()
            except Exception:
                logger.error("Could not pull repo")
                repo = git.Repo.clone_from(
                    RepoUrl.BITBUCKET_URL.value.format(repo_name=self.repo_full_name), self.repo_dir
                )
            logger.info("Repo already cached, copying")
        repo = git.Repo(self.repo_dir)
        return repo

    def clone_repo(self):
        """
        Initialize the repository after dataclass initialization.
        """

        self.git_repo = self.__clone()

    async def get_pr_details(self, pr_id: int):
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.

        Args:
            pr_id (int): The ID of the pull request.

        Returns:
            PullRequestResponse: An object containing details of the pull request.

        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """

        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")
        bitbucket_module = BitBucketModule(workspace=self.repo_full_name, pr_id=pr_id)
        return await bitbucket_module.get_pr_details()

    async def get_pr_diff(self, pr_id: int):
        """
        Get PR diff of a pull request from Bitbucket, Github or Gitlab.

        Args:
            pr_id (int): The ID of the pull request.

        Returns:
            str: The diff of a pull request

        Raises:
            ValueError: If the pull request diff cannot be retrieved.
        """

        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")
        bitbucket_module = BitBucketModule(workspace=self.repo_full_name, pr_id=pr_id)
        return await bitbucket_module.get_pr_diff()

    async def create_comment_on_pr(self, pr_id: int, comment: Union[str, dict]):
        """
        Create a comment on the pull request.

        Parameters:
        - pr_id (int): The ID of the pull request.
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")
        bitbucket_module = BitBucketModule(workspace=self.repo_full_name, pr_id=pr_id)
        if isinstance(comment, str):
            comment_payload = {"content": {"raw": comment}}
            return await bitbucket_module.create_comment_on_pr(comment_payload)
        else:
            if comment.get("file_path"):
                comment["file_path"] = re.sub(r"^[ab]/\s*", "", comment["file_path"])
                comment_payload = {
                    "content": {"raw": add_corrective_code(comment)},
                    "inline": {
                        "path": (
                            re.sub(r"^[ab]/\s*", "", comment["file_path"])
                            if re.match(r"^[ab]/\s*", comment.get("file_path"))
                            else comment.get("file_path")
                        ),
                        "to": comment.get("line_number"),
                    },
                }
                return await bitbucket_module.create_comment_on_pr(comment_payload)
