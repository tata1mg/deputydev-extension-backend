from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.utils.app_utils import get_task_response
from app.backend_common.utils.sanic_wrapper import Task
from app.main.blueprints.deputy_dev.constants import SCRIT_DEPRECATION_NOTIFICATION
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest


class BaseComment(ABC):
    def __init__(
        self,
        workspace: str,
        workspace_slug: str,
        repo_name: str,
        pr_id: str,
        auth_handler: AuthHandler,
        pr_details: PullRequestResponse = None,
        repo_id: Optional[int] = None,
    ) -> None:
        self.workspace = workspace
        self.pr_id = pr_id
        self.repo_name = repo_name
        self.pr_details: PullRequestResponse = pr_details
        self.branch_name = None
        self.meta_data = f"repo: {repo_name}, pr_id: {pr_id}, user_name: {workspace}"
        self.repo_id = repo_id
        self.auth_handler = auth_handler
        self.workspace_slug = workspace_slug
        self.repo_client = None

    @abstractmethod
    async def fetch_comment_thread(self, chat_request: ChatRequest) -> str:
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
    async def create_pr_review_comment(self, comment: Dict[str, Any], model: str) -> None:
        """creates comment on code files"""
        raise NotImplementedError()

    @abstractmethod
    async def create_pr_comment(self, comment: str, model: str) -> None:
        """creates comment on whole pr"""
        raise NotImplementedError()

    @abstractmethod
    async def create_comment_on_parent(self, comment: str, parent_id: str, model: str = "") -> None:
        """creates comment on whole pr"""
        raise NotImplementedError()

    @abstractmethod
    async def process_chat_comment(self, comment: str, chat_request: ChatRequest, add_note: bool = False) -> str:
        """process"""
        if add_note:
            # This is a temporary addition to convey the user of the deprecation of #scrit
            comment = f"{SCRIT_DEPRECATION_NOTIFICATION}\n\n{comment}"
        return comment

    async def create_bulk_comments(self, comments: List[Union[str, Dict[str, Any]]]) -> None:
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
                await self.create_pr_review_comment(comment, comment.get("model"))
            except Exception as e:  # noqa: BLE001
                AppLogger.log_error(f"Unable to create comment: {comment}: {e}")

    async def post_bots_comments(self, comments: List[Dict[str, Any]]) -> None:
        """
        Create two parallel tasks to comment on PR using multiple bots

        Args:
            comments(List): List of PR comments fetched from finetuned and foundation nodels
        Returns:
            None
        """
        batch_size = 10
        valid_comments = [comment for comment in comments if comment["is_valid"] is not False]
        batches = [valid_comments[i : i + batch_size] for i in range(0, len(valid_comments), batch_size)]
        for batch in batches:
            # Create tasks for the current batch
            tasks = [
                Task(
                    self.create_bulk_comments(comments=batch),
                    result_key="response",
                )
            ]

            await get_task_response(tasks)
