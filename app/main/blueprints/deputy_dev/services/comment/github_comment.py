from sanic.log import logger
from torpedo import CONFIG

from app.common.service_clients.github.github_repo_client import GithubRepoClient
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.helpers.github_comment_helper import (
    GithubCommentHelper,
)
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler
from app.main.blueprints.deputy_dev.utils import format_comment

config = CONFIG.config


class GithubComment(BaseComment):
    def __init__(
        self,
        workspace: str,
        workspace_slug: str,
        repo_name: str,
        pr_id: str,
        auth_handler: AuthHandler,
        pr_details: PullRequestResponse = None,
        repo_id=None,
    ):
        super().__init__(workspace, workspace_slug, repo_name, pr_id, auth_handler, pr_details, repo_id)
        self.repo_client = GithubRepoClient(
            workspace_slug=workspace_slug, repo=repo_name, pr_id=int(pr_id), auth_handler=auth_handler
        )
        self.comment_helper = GithubCommentHelper

    async def create_pr_comment(self, comment, model):
        """Create comment on whole PR"""
        comment_payload = {
            "body": format_comment(comment),
        }
        response = await self.repo_client.create_pr_comment(comment_payload)
        if not response or response.status_code != 201:
            logger.error(f"unable to make whole PR comment {self.meta_data}")
        return response

    async def create_pr_review_comment(self, comment, model):
        """Creates comments on PR lines"""
        logger.info(f"Comment payload: {comment}")
        comment["commit_id"] = self.pr_details.commit_id
        comment_payload = self.comment_helper.format_pr_review_comment(comment)

        response = await self.repo_client.create_pr_review_comment(payload=comment_payload)
        if response.status_code == 422:  # Gives 422 incase incorrect line or file is passed
            response = await self.create_pr_comment(comment_payload.get("body"), model)

        if not response or response.status_code != 201:
            logger.error(f"unable to comment on github PR {self.meta_data}")
        comment["scm_comment_id"] = str(response.json()["id"])
        comment["llm_source_model"] = model

    async def fetch_comment_thread(self, chat_request, depth=0):
        """
        Fetches the comment thread for a comment_id

        Parameters:
        - comment_id (str): Comment id

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment_thread = ""
        first_parent_id = chat_request.comment.parent

        if not first_parent_id:
            return comment_thread

        try:
            all_pr_comments = await self.repo_client.get_pr_comments()

            for comment in all_pr_comments:
                if comment.get("in_reply_to_id") == first_parent_id and comment["id"] != chat_request.comment.id:
                    comment_thread += "\n" + comment["body"]

            return comment_thread
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing fetch_comment_thread : {e}")
            return ""

    async def process_chat_comment(self, comment, chat_request: ChatRequest, add_note: bool = False):
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment = await super().process_chat_comment(comment, chat_request, add_note)
        have_parent = True if chat_request.comment.parent else False
        comment_payload = self.comment_helper.format_chat_comment(comment, chat_request, have_parent=have_parent)
        await self.create_comment_on_thread(comment_payload)

    async def create_comment_on_thread(self, comment_payload):
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        logger.info(f"Comment payload:{comment_payload}")
        response = await self.repo_client.create_pr_review_comment(payload=comment_payload)
        return response
