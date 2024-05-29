import asyncio
import os
import re
import shutil
from functools import cached_property
from typing import List, Union

import git
from sanic.log import logger
from torpedo import CONFIG, Task

from app.constants import RepoUrl
from app.constants.constants import LLMModels
from app.constants.repo import VCSTypes
from app.dao.repo import PullRequestResponse
from app.utils import (
    add_corrective_code,
    get_task_response,
    get_time_difference,
    parse_collection_name,
)

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

        # we only get return code 0 or 1 from process, where 0 means everything is working fine and 1
        # means something went wrong while performing the task, we don't get any specific error message,
        # so we are adding our own custom message for the same
        if return_code == 0:
            logger.info("Cloning completed")
            repo = git.Repo(self.repo_dir)
            return repo
        else:
            raise Exception("Something went wrong while cloning the repo")

    async def clone_repo(self):
        """
        Initialize the repository after dataclass initialization.
        """
        try:
            self.git_repo = await self.__clone()
            return self.git_repo
        except Exception as e:
            raise Exception(e)

    def parse_pr_detail(self, pr_detail: PullRequestResponse, request_time: str) -> PullRequestResponse:
        """
        Parse pull request details to determine if it was created within a certain time threshold.

        Parameters:
        pr_detail (PullRequestResponse): The pull request details including creation time.
        request_time (str): The time of the request.

        Returns:
        PullRequestResponse: The updated pull request details with 'created' flag adjusted based on the time difference.
        """
        time_difference = get_time_difference(pr_detail.created_on, request_time)
        if time_difference > 15:
            pr_detail.created = False
        return pr_detail

    async def get_pr_details(self, pr_id: int, request_time: str) -> PullRequestResponse:
        """
        Get details of a pull request from Bitbucket, Github or Gitlab.

        Args:
            pr_id (int): The ID of the pull request.
            request_time (str): Time when request was generated

        Returns:
            PullRequestResponse: An object containing details of the pull request.

        Raises:
            ValueError: If the pull request details are invalid or cannot be retrieved.
        """
        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")
        bitbucket_module = BitBucketModule(workspace=self.repo_full_name, pr_id=pr_id)
        pr_detail = await bitbucket_module.get_pr_details()
        return self.parse_pr_detail(pr_detail, request_time)

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

    async def create_comment_on_pr(self, pr_id: int, comment: Union[str, dict], model: str):
        """
        Create a comment on the pull request.

        Parameters:
        - pr_id (int): The ID of the pull request.
        - comment (str): The comment that needs to be added
        - model(str): model which was used to retrieve comments. Helps identify the bot to post comment

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        if self.vcs_type != VCSTypes.bitbucket.value:
            raise ValueError("Unsupported VCS type. Only Bitbucket is supported.")
        bitbucket_module = BitBucketModule(workspace=self.repo_full_name, pr_id=pr_id)
        if isinstance(comment, str):
            comment_payload = {"content": {"raw": comment}}
            return await bitbucket_module.create_comment_on_pr(comment_payload, model)
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
                logger.info(f"Comment payload: {comment_payload}")

                return await bitbucket_module.create_comment_on_pr(comment_payload, model)

    async def create_bulk_comments(self, pr_id: int, comments: List[Union[str, dict]], model: str) -> None:
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
                await self.create_comment_on_pr(pr_id, comment, model)
            except Exception as e:
                logger.error(f"Unable to create comment on PR {pr_id}: {e}")

    async def post_bots_comments(self, response, pr_id):
        """
        Create two parallel tasks to comment on PR using multiple bots

        Args:
            response(dict): dict of PR comments fetched from finetuned and foundation nodels
            pr_id (int): PR ID

        Returns:
            None
        """
        tasks = [
            Task(
                self.create_bulk_comments(
                    pr_id=pr_id,
                    comments=response.get("finetuned_comments"),
                    model=LLMModels.FinetunedModel.value,
                ),
                result_key="finetuned_comments",
            ),
            Task(
                self.create_bulk_comments(
                    pr_id=pr_id,
                    comments=response.get("foundation_comments"),
                    model=LLMModels.FoundationModel.value,
                ),
                result_key="foundation_comments",
            ),
        ]
        await get_task_response(tasks)
