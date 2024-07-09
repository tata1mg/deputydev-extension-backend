import asyncio
import os
import re
import shutil
from functools import cached_property
from typing import List, Union

import git
from sanic.log import logger
from torpedo import CONFIG, Task

from app.common.utils.app_utils import get_task_response
from app.main.blueprints.deputy_dev.constants import LLMModels
from app.main.blueprints.deputy_dev.constants.constants import COMMENTS_DEPTH
from app.main.blueprints.deputy_dev.constants.repo import RepoUrl, VCSTypes
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.atlassian.bitbucket.bitbucket import (
    BitBucketModule,
)
from app.main.blueprints.deputy_dev.utils import format_comment, parse_collection_name


class RepoModule:
    """Represents a module for handling repositories."""

    def __init__(self, repo_full_name: str, pr_id: int, vcs_type: VCSTypes, branch_name: str = None) -> None:
        self.repo_full_name = repo_full_name
        self.pr_id = pr_id
        self.vcs_type = vcs_type
        self.branch_name = branch_name
        self.pr_details = None
        if self.vcs_type == VCSTypes.bitbucket.value:
            self.bitbucket_module = BitBucketModule(workspace=repo_full_name, pr_id=pr_id)
        else:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")

    async def initialize(self):
        self.pr_details = await self.get_pr_details()
        self.branch_name = self.pr_details.branch_name

    def get_pr_id(self):
        return self.pr_id

    def get_pr_creation_time(self):
        return self.pr_details.created_on

    def set_branch_name(self, branch_name):
        self.branch_name = branch_name

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

    async def __clone(self) -> git.Repo:
        """
        This is a private method to clone the repository if it doesn't exist locally or pull updates if it does.
        """

        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")

        process = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--branch",
            self.branch_name,
            RepoUrl.BITBUCKET_URL.value.format(repo_name=self.repo_full_name),
            self.repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return_code = await process.wait()
        if return_code == 0:
            logger.info("Cloning completed")
        repo = git.Repo(self.repo_dir)
        return repo

    async def clone_repo(self):
        """
        Initialize the repository after dataclass initialization.
        """
        try:
            self.git_repo = await self.__clone()
            return self.git_repo
        except Exception as e:
            raise Exception(e)

    async def get_pr_details(self) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.
        Args:
        Returns:
            PullRequestResponse: An object containing details of the pull request.
        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """

        return await self.bitbucket_module.get_pr_details()

    async def get_pr_diff(self):
        """
        Get PR diff of a pull request from Bitbucket, Github or Gitlab.

        Args:
        Returns:
            str: The diff of a pull request

        Raises:
            ValueError: If the pull request diff cannot be retrieved.
        """

        return await self.bitbucket_module.get_pr_diff()

    async def create_comment_on_pr(self, comment: Union[str, dict], model: str):
        """
        Create a comment on the pull request.

        Parameters:
        - comment (str): The comment that needs to be added
        - model(str): model which was used to retrieve comments. Helps identify the bot to post comment

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        if isinstance(comment, str):
            comment_payload = {"content": {"raw": comment}}
            return await self.bitbucket_module.create_comment_on_pr(comment_payload, model)
        else:
            if comment.get("file_path"):
                comment["file_path"] = re.sub(r"^[ab]/\s*", "", comment["file_path"])
                comment_payload = {
                    "content": {"raw": format_comment(comment)},
                    "inline": {
                        "path": (
                            re.sub(r"^[ab]/\s*", "", comment["file_path"])
                            if re.match(r"^[ab]/\s*", comment.get("file_path"))
                            else comment.get("file_path")
                        )
                    },
                }
                if int(comment.get("line_number")) >= 0:
                    comment_payload["inline"]["to"] = int(comment.get("line_number"))
                else:
                    comment_payload["inline"]["from"] = -1 * int(comment.get("line_number"))
                logger.info(f"Comment payload: {comment_payload}")
                return await self.bitbucket_module.create_comment_on_pr(comment_payload, model)

    async def create_bulk_comments(self, comments: List[Union[str, dict]], model: str) -> None:
        """
        Iterate over each comment in pull request and post that comment on PR.

        Parameters:
        - pr_id (int): The ID of the pull request.
        - comments (List[Union[str, dict]]): A list of comments to be added
        - model(str): model which was used to retrieve comments. Helps identify the bot to post comment

        Returns:
        - None
        """
        for comment in comments:
            try:
                await self.create_comment_on_pr(comment, model)
            except Exception as e:
                logger.error(f"Unable to create comment on PR {self.pr_id}: {e}")

    async def post_bots_comments(self, response):
        """
        Create two parallel tasks to comment on PR using multiple bots

        Args:
            response(dict): dict of PR comments fetched from finetuned and foundation nodels
        Returns:
            None
        """
        tasks = [
            Task(
                self.create_bulk_comments(
                    comments=response.get("finetuned_comments"),
                    model=LLMModels.FinetunedModel.value,
                ),
                result_key="finetuned_comments",
            ),
            Task(
                self.create_bulk_comments(
                    comments=response.get("foundation_comments"),
                    model=LLMModels.FoundationModel.value,
                ),
                result_key="foundation_comments",
            ),
        ]
        await get_task_response(tasks)

    async def fetch_comment_thread(self, comment_id, depth=0):
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        try:
            if depth >= COMMENTS_DEPTH:
                return ""  # Stop recursion when depth exceeds 7

            response = await self.bitbucket_module.get_comment_details(comment_id)
            comment_thread = ""
            if response.status_code == 200:
                comment_data = response.json()
                comment_thread += comment_data["content"]["raw"]
                if "parent" in comment_data:
                    parent_comment_id = comment_data["parent"]["id"]
                    parent_thread = await self.fetch_comment_thread(parent_comment_id, depth + 1)
                    comment_thread += "\n" + parent_thread
            return comment_thread
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing fetch_comment_thread : {e}")
            return ""

    async def create_comment_on_comment(self, comment, comment_data):
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment_payload = {
            "content": {"raw": format_comment(comment)},
            "parent": {"id": comment_data["parent"]},
            "inline": {"path": comment_data["path"]},
        }
        logger.info(f"Comment payload:{comment_payload}")
        response = await self.bitbucket_module.create_comment_on_pr(comment_payload, LLMModels.FoundationModel.value)
        return response

    async def create_comment_on_line(self, comment: dict):
        """
        Create a comment on a line in a file in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        if comment.get("file_path"):
            comment["file_path"] = re.sub(r"^[ab]/\s*", "", comment["file_path"])
        comment_payload = {
            "content": {"raw": format_comment(comment)},
            "inline": {
                "path": re.sub(r"^[ab]/\s*", "", comment["file_path"])
                if re.match(r"^[ab]/\s*", comment.get("file_path"))
                else comment.get("file_path"),
                "to": comment.get("line_number"),
            },
        }
        logger.info(f"Comment payload: {comment_payload}")
        response = await self.bitbucket_module.create_comment_on_pr(comment_payload, LLMModels.FoundationModel.value)
        return response
