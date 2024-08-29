from sanic.log import logger
from torpedo import CONFIG

from app.common.service_clients.bitbucket.bitbucket_repo_client import (
    BitbucketRepoClient,
)
from app.main.blueprints.deputy_dev.constants.constants import COMMENTS_DEPTH
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.helpers.bitbucket_comment_helper import (
    BitbucketCommentHelper,
)

config = CONFIG.config


class BitbucketComment(BaseComment):
    def __init__(self, workspace: str, repo_name: str, pr_id: str, pr_details: PullRequestResponse = None):
        super().__init__(workspace, repo_name, pr_id, pr_details)
        self.repo_client = BitbucketRepoClient(workspace, repo_name, int(pr_id))
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

            response = await self.repo_client.get_comment_details(comment_id)
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

    async def create_pr_comment(self, comment: str, model: str):
        comment_payload = {"content": {"raw": comment}}
        return await self.repo_client.create_comment_on_pr(comment_payload, model)

    async def create_pr_review_comment(self, comment: dict, model):
        comment_payload = self.comment_helper.format_pr_review_comment(comment)
        line_number = int(comment.get("line_number").split(",")[0]) or 1
        if line_number >= 0:
            comment_payload["inline"]["to"] = line_number
        else:
            comment_payload["inline"]["from"] = -1 * line_number
        logger.info(f"Comment payload: {comment_payload}")
        result = await self.repo_client.create_comment_on_pr(comment_payload, model)
        comment["scm_comment_id"] = result["id"]
        comment["llm_source_model"] = model
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
