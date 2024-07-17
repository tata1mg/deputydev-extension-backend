from sanic.log import logger

from app.common.service_clients.github.github_repo_client import GithubRepoClient
from app.main.blueprints.deputy_dev.constants import LLMModels
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.helpers.github_comment_helper import (
    GithubCommentHelper,
)
from app.main.blueprints.deputy_dev.utils import format_comment


class GithubComment(BaseComment):
    def __init__(self, workspace: str, repo_name: str, pr_id: str, pr_details: PullRequestResponse = None):
        super().__init__(workspace, repo_name, pr_id, pr_details)
        self.repo_client = GithubRepoClient
        self.comment_helper = GithubCommentHelper

    async def create_pr_comment(self, comment, model):
        """Create comment on whole PR"""
        comment_payload = {
            "body": format_comment(comment),
        }
        response = await self.repo_client.create_pr_comment(self.workspace, self.repo_name, self.pr_id, comment_payload)
        if not response or response.status_code != 201:
            logger.error(f"unable to make whole PR comment {self.meta_data}")

    async def create_pr_review_comment(self, comment, model):
        """Creates comments on PR lines"""
        comment["commit_id"] = self.pr_details.commit_id
        comment_payload = self.comment_helper.format_pr_review_comment(comment)
        logger.info(f"Comment payload: {comment_payload}")

        response = await self.repo_client.create_pr_review_comment(
            user_name=self.workspace, pr_id=self.pr_id, repo_name=self.repo_name, payload=comment_payload
        )
        if not response or response.status_code != 201:
            logger.error(f"unable to comment on github PR {self.meta_data}")

    async def fetch_comment_thread(self, comment_id, depth=0):
        """
        Fetches the comment thread for a comment_id

        Parameters:
        - comment_id (str): Comment id

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment_thread = ""
        try:
            response = await self.repo_client.get_comment_thread(
                user_name=self.workspace, repo_name=self.repo_name, comment_id=comment_id
            )
            if not response or response.status_code != 201:
                logger.error(f"unable to comment on github PR {self.meta_data}")
            else:
                comment_thread = response.json()["body"]
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing fetch_comment_thread : {e}")
        return comment_thread

    async def process_chat_comment(self, comment, chat_request: ChatRequest):
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment = await super().process_chat_comment(comment, chat_request)
        if chat_request.comment.path:
            comment_payload = self.comment_helper.format_chat_comment(comment, chat_request)
            await self.create_pr_review_comment(comment_payload, model=LLMModels.FoundationModel.value)
        else:
            await self.create_pr_comment(comment, model=LLMModels.FoundationModel.value)
