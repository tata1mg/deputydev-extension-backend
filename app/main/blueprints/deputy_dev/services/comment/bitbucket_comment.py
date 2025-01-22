from sanic.log import logger
from torpedo import CONFIG

from app.backend_common.service_clients.bitbucket import BitbucketRepoClient
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.common.utils.app_logger import AppLogger
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.helpers.bitbucket_comment_helper import (
    BitbucketCommentHelper,
)
from app.main.blueprints.deputy_dev.utils import format_chat_comment_thread_comment

config = CONFIG.config


class BitbucketComment(BaseComment):
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
        self.repo_client = BitbucketRepoClient(workspace_slug, repo_name, int(pr_id), auth_handler=auth_handler)
        self.comment_helper = BitbucketCommentHelper

    async def create_comment_on_line(self, comment: dict):
        """
        Create a comment on a line in a file in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment_payload = self.comment_helper.format_pr_review_inline_comment(comment)
        logger.info(f"Comment payload: {comment_payload}")
        response = await self.repo_client.create_comment_on_pr(
            comment_payload, config.get("FEATURE_MODELS").get("PR_CHAT")
        )
        return response

    async def fetch_comment_thread(self, chat_request):
        """
        Fetches comment thread by finding root node and building thread recursively.

        Example:
        comment1 (root)
        └── comment2
            ├── comment3
            │   └── comment4
            ├── comment5 (#dd)
            └── comment6
                └── comment7
        """
        if not chat_request.comment.parent:
            return ""

        try:
            # Fetch all comments once
            all_comments = await self.repo_client.get_pr_comments()  # in ascending order of created_at
            if not all_comments:
                return ""

            comment_map = {comment["id"]: comment for comment in all_comments}

            children_map = {}
            for comment in all_comments:
                parent_id = comment.get("parent", {}).get("id")
                if parent_id:
                    if parent_id not in children_map:
                        children_map[parent_id] = []
                    children_map[parent_id].append(comment)

            root_comment_id = chat_request.comment.parent

            while root_comment_id:
                current_comment = comment_map.get(root_comment_id)
                parent_id = current_comment.get("parent", {}).get("id")
                if current_comment.get("parent", {}).get("id"):
                    root_comment_id = parent_id
                else:
                    break

            # Build thread starting from root comment
            thread_comments = []
            await self._build_comment_thread(
                root_comment_id, comment_map, children_map, thread_comments, chat_request.comment.id
            )

            if not thread_comments:
                return ""

            # Comments are already in ascending order, so childeren_map maintains order of insertion
            # So thread comments will always be in sorted order of time as parent comments are processed before children and siblings in order of time as they are present in comment_map
            thread = ""
            for comment in thread_comments:
                formatted_comment = format_chat_comment_thread_comment(comment["content"]["raw"]) + "\n"
                thread += formatted_comment
            return thread

        except Exception as e:
            AppLogger.log_warn(f"Error processing comment thread: {e}")
            return ""

    async def _build_comment_thread(self, comment_id, comment_map, children_map, thread_comments, request_comment_id):
        """
        Recursively builds comment thread starting from root.

        Args:
            comment_id: Current comment ID
            comment_map: Map of comment IDs to comments
            children_map: Map of parent IDs to children
            thread_comments: List to collect thread comments
            request_comment_id: ID of the #dd comment to exclude
        """
        try:
            # Process current comment if not #dd
            if comment_id != request_comment_id:
                current_comment = comment_map.get(comment_id)
                if current_comment and current_comment.get("content", {}).get("raw"):
                    thread_comments.append(current_comment)

            # Process all children recursively
            for child in children_map.get(comment_id, []):
                if child["id"] != request_comment_id:
                    await self._build_comment_thread(
                        child["id"], comment_map, children_map, thread_comments, request_comment_id
                    )
        except Exception as e:
            AppLogger.log_error(f"Error building thread from comment {comment_id}: {e}")

    async def create_pr_comment(self, comment: str, model: str):
        comment_payload = {"content": {"raw": comment}}
        return await self.repo_client.create_comment_on_pr(comment_payload, model)

    async def create_comment_on_parent(self, comment: str, parent_id, model: str = ""):
        """creates comment on whole pr"""
        comment_payload = {"content": {"raw": comment}, "parent": {"id": parent_id}}
        return await self.repo_client.create_comment_on_pr(comment_payload, model)

    async def create_pr_review_comment(self, comment: dict, model):
        logger.info(f"Comment payload: {comment}")
        comment_payload = self.comment_helper.format_pr_review_comment(comment)

        result = await self.repo_client.create_comment_on_pr(comment_payload, model)
        result_json = await result.json()
        comment["scm_comment_id"] = result_json["id"]
        return result

    async def process_chat_comment(self, comment, chat_request: ChatRequest, add_note: bool = False):
        comment = await super().process_chat_comment(comment, chat_request, add_note)
        if chat_request.comment.parent:
            await self.create_comment_on_thread(comment, chat_request)
        elif chat_request.comment.line_number_from or chat_request.comment.line_number_to:
            comment_payload = self.comment_helper.format_chat_comment(comment, chat_request)
            await self.create_comment_on_line(comment_payload)
        else:
            await self.create_pr_comment(comment, config.get("FEATURE_MODELS").get("PR_CHAT"))

    async def create_comment_on_thread(self, comment, chat_request: ChatRequest):
        """
        Create a comment on a parent comment in pull request.

        Parameters:
        - comment (str): The comment that needs to be added

        Returns:
        - Dict[str, Any]: A dictionary containing the response from the server.
        """
        comment_payload = self.comment_helper.format_chat_thread_comment(comment, chat_request)
        logger.info(f"Comment payload:{comment_payload}")
        response = await self.repo_client.create_comment_on_pr(
            comment_payload, config.get("FEATURE_MODELS").get("PR_CHAT")
        )
        return response
