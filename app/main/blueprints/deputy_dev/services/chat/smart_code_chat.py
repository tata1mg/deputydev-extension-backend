import asyncio

from sanic.log import logger
from torpedo import CONFIG

from app.common.services.openai.client import LLMClient
from app.common.utils.app_utils import build_openai_conversation_message
from app.main.blueprints.deputy_dev.constants import TAGS, LLMModels
from app.main.blueprints.deputy_dev.constants.prompts.v1.system_prompts import (
    CHAT_COMMENT_PROMPT,
)
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.atlassian.jira.jira_manager import (
    JiraManager,
)
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.webhook.chat_webhook import ChatWebhook
from app.main.blueprints.deputy_dev.utils import format_code_blocks


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict, vcs_type: str):
        comment_payload = ChatWebhook.parse_payload(payload, vcs_type)
        logger.info(f"Comment payload: {comment_payload}")
        asyncio.ensure_future(cls.handle_chat_request(comment_payload, vcs_type=vcs_type))

    @classmethod
    async def handle_chat_request(cls, chat_request: ChatRequest, vcs_type):
        repo = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            pr_id=chat_request.repo.pr_id,
            workspace=chat_request.repo.workspace,
        )

        comment_service = await CommentFactory.comment(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            pr_id=chat_request.repo.pr_id,
            workspace=chat_request.repo.workspace,
            pr_details=repo.pr_details,
        )

        comment = chat_request.comment.raw.lower()
        # we are checking whether the comment starts with any of the tags or not
        if any(comment.startswith(tag) for tag in TAGS):
            logger.info(f"Processing the comment: {comment} , with payload : {chat_request}")

            diff = await repo.get_pr_diff()
            user_story_description = await JiraManager(issue_id=repo.pr_details.issue_id).get_description_text()
            get_comment_thread = await comment_service.fetch_comment_thread(chat_request.comment.id)

            context = (
                f"Comment Thread : {get_comment_thread} , questions: {comment}\n PR diff: {diff}\n"
                f"User story description - {user_story_description}. Use this to get context of business logic for which change is made."
            )
            await cls.get_chat_comments(context, chat_request, comment_service)
            logger.info(f"Chat processing completed: {comment} , with payload : {chat_request}")

    @classmethod
    async def get_chat_comments(cls, context, chat_request: ChatRequest, comment_service):
        llm_comment_response = await cls.get_comments_from_llm(context, LLMModels.FoundationModel.value)
        logger.info(f"Process chat comment response: {llm_comment_response}")
        await comment_service.process_chat_comment(comment=llm_comment_response, chat_request=chat_request)

    @classmethod
    async def get_comments_from_llm(cls, comment_data: str, model: str) -> str:
        """
        Makes a call to OpenAI chat completion API with a specific model and conversation messages.

        Parameters:
        - comment_data (str): Comment details that needs to be passed to llm
        - model: GPT model Name defined in config file.

        Returns:
        - formatted_comment (str): Response from the llm server for the comment made on PR.
        """
        client, model_config, context = LLMClient(), CONFIG.config.get(model), CHAT_COMMENT_PROMPT

        conversation_message = build_openai_conversation_message(system_message=context, user_message=comment_data)

        response = await client.get_client_response(
            conversation_message=conversation_message, model=model_config.get("MODEL"), response_type="text"
        )
        formatted_comment = format_code_blocks(response.content)
        return formatted_comment
