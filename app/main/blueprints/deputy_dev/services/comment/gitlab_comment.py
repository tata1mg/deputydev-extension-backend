from typing import Any, Dict, Optional

from sanic.log import logger

from app.backend_common.service_clients.gitlab.gitlab_repo_client import (
    GitlabRepoClient,
)
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.helpers.gitlab_comment_helper import (
    GitlabCommentHelper,
)
from app.main.blueprints.deputy_dev.utils import format_comment

config = CONFIG.config


class GitlabComment(BaseComment):
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
        super().__init__(workspace, workspace_slug, repo_name, pr_id, auth_handler, pr_details, repo_id=repo_id)
        self.repo_client = GitlabRepoClient(pr_id=pr_id, project_id=self.repo_id, auth_handler=auth_handler)
        self.comment_helper = GitlabCommentHelper

    async def create_pr_comment(self, comment: Dict[str, Any], model: str) -> None:
        """Create comment on whole PR"""
        comment_payload = {
            "body": format_comment(comment),
        }
        response = await self.repo_client.create_pr_comment(comment_payload)
        if not response or response.status_code != 201:
            logger.error(f"unable to make whole PR comment {self.meta_data}")
        return response

    async def create_comment_on_parent(self, comment: Dict[str, Any], parent_id: str, model: str = "") -> None:
        """creates comment on whole pr"""
        comment_payload = {"body": format_comment(comment)}
        response = await self.repo_client.create_comment_on_parent(comment_payload, parent_id)
        if not response or response.status_code != 201:
            logger.error(f"unable to make whole PR comment {self.meta_data}")
        return response

    async def create_pr_review_comment(self, comment: Dict[str, Any], model: str) -> None:
        """Creates comments on PR lines"""
        logger.info(f"Comment payload: {comment}")
        comment["commit_id"] = self.pr_details.commit_id

        comment_payload = self.comment_helper.format_pr_review_comment(comment, self.pr_details.diff_refs)
        response = await self.repo_client.create_pr_review_comment(comment_payload=comment_payload)
        if response.status_code == 400:  # Gives 422 incase incorrect line or file is passed
            response = await self.create_pr_comment(comment_payload.get("body"), model)

        if not response or response.status_code != 201:
            logger.error(f"unable to comment on github PR {self.meta_data}")
        response_json = await response.json()
        comment["scm_comment_id"] = str(response_json["id"])

    async def fetch_comment_thread(self, chat_request: ChatRequest) -> str:
        """
        Fetches the comment thread for a comment_id

        Parameters:
        - comment_id (str): Comment id

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """

        comment_thread = ""
        try:
            discussion_thread_comments = await self.repo_client.get_discussion_comments(chat_request.comment.parent)

            for comment in discussion_thread_comments:
                if comment.get("id") != chat_request.comment.id:
                    comment_thread += "\n" + comment["body"]

            return comment_thread
        except Exception as e:  # noqa: BLE001
            logger.error(f"An unexpected error occurred while processing fetch_comment_thread : {e}")
            return ""

    async def process_chat_comment(self, comment: str, chat_request: ChatRequest, add_note: bool = False) -> None:
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment = await super().process_chat_comment(comment, chat_request, add_note)
        comment_payload = {"body": comment}
        await self.create_comment_on_thread(comment_payload, chat_request.comment.parent)

    async def create_comment_on_thread(self, comment_payload: Dict[str, Any], discussion_id: str) -> Dict[str, Any]:
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        logger.info(f"Comment payload:{comment_payload}")
        response = await self.repo_client.create_discussion_comment(comment_payload, discussion_id)
        return response
