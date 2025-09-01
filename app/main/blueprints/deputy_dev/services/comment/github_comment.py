from typing import Any, Dict, Optional

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value
from sanic.log import logger

from app.backend_common.service_clients.github.github_repo_client import (
    GithubRepoClient,
)
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.helpers.github_comment_helper import (
    GithubCommentHelper,
)
from app.main.blueprints.deputy_dev.utils import (
    format_chat_comment_thread_comment,
    format_comment,
)

config = CONFIG.config


class GithubComment(BaseComment):
    def __init__(
        self,
        workspace: str,
        workspace_slug: str,
        repo_name: str,
        pr_id: str,
        auth_handler: AuthHandler,
        pr_details: Optional[PullRequestResponse] = None,
        repo_id: Optional[int] = None,
    ) -> None:
        super().__init__(workspace, workspace_slug, repo_name, pr_id, auth_handler, pr_details, repo_id)
        self.repo_client = GithubRepoClient(
            workspace_slug=workspace_slug, repo=repo_name, pr_id=int(pr_id), auth_handler=auth_handler
        )
        self.comment_helper = GithubCommentHelper

    async def create_pr_comment(self, comment: Dict[str, Any], model: str) -> None:
        """Create comment on whole PR"""
        comment_payload = {
            "body": format_comment(comment),
        }
        response = await self.repo_client.create_pr_comment(comment_payload)
        if not response or response.status_code != 201:
            logger.error(f"unable to make whole PR comment {self.meta_data}")
        return response

    async def create_comment_on_parent(self, comment: str, parent_id: str, model: str = "") -> None:
        """creates comment on whole pr"""
        if get_context_value("is_issue_comment"):
            comment_payload = {"body": format_comment(comment)}
            response = await self.repo_client.create_issue_comment(comment_payload, parent_id)
        else:
            comment_payload = {"body": format_comment(comment), "in_reply_to": parent_id}
            response = await self.repo_client.create_pr_comment(comment_payload)
        if not response or response.status_code != 201:
            logger.error(f"unable to make whole PR comment {self.meta_data}")
        return response

    async def create_pr_review_comment(self, comment: Dict[str, Any], model: str) -> None:
        """Creates comments on PR lines"""
        logger.info(f"Comment payload: {comment}")
        comment["commit_id"] = self.pr_details.commit_id
        comment_payload = self.comment_helper.format_pr_review_comment(comment)

        response = await self.repo_client.create_pr_review_comment(payload=comment_payload)
        if response.status_code == 422:  # Gives 422 incase incorrect line or file is passed
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
        first_parent_id = chat_request.comment.parent

        if not first_parent_id:
            return comment_thread

        try:
            all_pr_comments = await self.repo_client.get_pr_comments()  # in ascending order of created_at
            parent_comment_body = ""
            for comment in all_pr_comments:
                # In github all comments in a root comment in a thread have same parent as root comment.
                # So collecting all comments with same parent as chat_request parent, as they belong to same thread.
                if comment.get("in_reply_to_id") == first_parent_id and comment["id"] != chat_request.comment.id:
                    comment_thread += "\n" + format_chat_comment_thread_comment(comment["body"])
                if comment.get("id") == first_parent_id:
                    parent_comment_body = format_chat_comment_thread_comment(comment["body"]) + "\n"

            comment_thread = parent_comment_body + comment_thread

            return comment_thread
        except KeyError as e:
            AppLogger.log_warn(f"Missing required field in comment data: {e}")
            return ""
        except ValueError as e:
            AppLogger.log_warn(f"Invalid data format in comments: {e}")
            return ""

    async def process_chat_comment(self, comment: str, chat_request: ChatRequest, add_note: bool = False) -> None:
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        if get_context_value("is_issue_comment"):
            comment_payload = {"body": comment}
            await self.repo_client.create_issue_comment(comment_payload, chat_request.comment.id)
            return
        comment = await super().process_chat_comment(comment, chat_request, add_note)
        have_parent = True if chat_request.comment.parent else False
        comment_payload = self.comment_helper.format_chat_comment(comment, chat_request, have_parent=have_parent)
        await self.create_comment_on_thread(comment_payload)

    async def create_comment_on_thread(self, comment_payload: Dict[str, Any]) -> Dict[str, Any]:
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
