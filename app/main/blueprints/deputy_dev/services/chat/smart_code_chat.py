import asyncio

from sanic.log import logger
from torpedo import CONFIG

from app.common.services.openai.client import LLMClient
from app.common.utils.app_utils import build_openai_conversation_message
from app.main.blueprints.deputy_dev.constants import LLMModels
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.atlassian.jira.jira_manager import (
    JiraManager,
)
from app.main.blueprints.deputy_dev.services.repo import RepoModule
from app.main.blueprints.deputy_dev.utils import format_code_blocks, get_comment


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict):
        comment_payload = get_comment(payload)
        logger.info(f"Comment payload: {comment_payload}")
        asyncio.ensure_future(cls.identify_annotation(payload, comment_payload))
        return

    @classmethod
    async def identify_annotation(cls, payload, comment_payload):
        repo = RepoModule(
            repo_full_name=payload["repository"]["full_name"],
            pr_id=payload["pullrequest"]["id"],
            vcs_type=VCSTypes.bitbucket.value,
        )
        await repo.initialize()

        tag = "#scrit"
        comment = comment_payload.get("comment").lower()
        if tag in comment:
            logger.info(f"Processing the comment: {comment} , with payload : {payload}")

            diff = await repo.get_pr_diff()
            user_story_description = await JiraManager(issue_id=repo.pr_details.issue_id).get_description_text()
            get_comment_thread = await repo.fetch_comment_thread(payload["comment"]["id"])

            context = (
                f"Comment Thread : {get_comment_thread} , questions: {comment}\n PR diff: {diff}\n"
                f"User story description - {user_story_description}. Use this to get context of business logic for which change is made."
            )
            await cls.process_chat_comment(context, comment_payload, repo)

    @classmethod
    async def process_chat_comment(cls, context, comment_payload, repo: RepoModule):
        logger.info("process_chat_comment")
        comment_response = await cls.comment_processor(context, LLMModels.FoundationModel.value)
        logger.info(f"Process chat comment response: {comment_response}")
        # This validation will determine the origin of the request,
        # such as whether it's a reply to an existing comment or a PR-level comment.
        if "parent" in comment_payload:
            await repo.create_comment_on_comment(comment_response, comment_payload)
        elif "line_number" in comment_payload:
            inline_response = {}
            inline_response["comment"] = comment_response
            inline_response["file_path"] = comment_payload["path"]
            inline_response["line_number"] = comment_payload["line_number"]
            await repo.create_comment_on_line(inline_response)
        else:
            await repo.create_comment_on_pr(comment_response)

    async def comment_processor(comment_data: str, model: str) -> str:
        """
        Makes a call to OpenAI chat completion API with a specific model and conversation messages.

        Parameters:
        - comment_data (str): Comment details that needs to be passed to llm
        - model: GPT model Name defined in config file.

        Returns:
        - formatted_comment (str): Response from the llm server for the comment made on PR.
        """
        client = LLMClient()
        model_config = CONFIG.config.get(model)
        context = (
            "Your name is SCRIT, receiving a user's comment thread carefully examine the smart code review analysis. If "
            "the comment involves inquiries about code improvements or other technical discussions, evaluate the provided "
            "pull request (PR) diff and offer appropriate resolutions. Otherwise, respond directly to the posed question "
            "without delving into the PR diff. include all the corrective_code inside ``` CODE ``` markdown"
        )
        conversation_message = build_openai_conversation_message(system_message=context, user_message=comment_data)
        response = await client.get_client_response(
            conversation_message=conversation_message, model=model_config.get("MODEL"), response_type="text"
        )
        formatted_comment = format_code_blocks(response.content)
        return formatted_comment
