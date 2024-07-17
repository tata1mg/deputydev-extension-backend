from abc import ABC, abstractmethod
from typing import List, Union

from sanic.log import logger
from torpedo import Task

from app.common.utils.app_utils import get_task_response
from app.main.blueprints.deputy_dev.constants import LLMModels
from app.main.blueprints.deputy_dev.constants import SCRIT_DEPRECATION_NOTIFICATION
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse


class BaseComment(ABC):
    def __init__(self, workspace: str, repo_name: str, pr_id: str, pr_details: PullRequestResponse = None):
        self.workspace = workspace
        self.pr_id = pr_id
        self.repo_name = repo_name
        self.pr_details: PullRequestResponse = pr_details
        self.branch_name = None
        self.meta_data = f"repo: {repo_name}, pr_id: {pr_id}, user_name: {workspace}"

    @abstractmethod
    async def fetch_comment_thread(self, comment_id, depth=0):
        """
        Fetches comment thread
        Args:
            Returns:
        PullRequestResponse:
            An object containing details of the pull request.
        Raises:
        """
        raise NotImplementedError()

    @abstractmethod
    async def create_pr_review_comment(self, comment: dict, model):
        """creates comment on code files"""
        raise NotImplementedError()

    @abstractmethod
    async def create_pr_comment(self, comment: str, model: str):
        """creates comment on whole pr"""
        raise NotImplementedError()

    @abstractmethod
    async def process_chat_comment(self, comment, chat_request: ChatRequest):
        """process"""
        # This is a temporary addition to convey the user of the deprecation of #scrit
        comment = f"{SCRIT_DEPRECATION_NOTIFICATION}\n\n{comment}"
        return comment

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
                await self.create_pr_review_comment(comment, model)
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
