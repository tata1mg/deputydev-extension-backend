import asyncio

from sanic.log import logger
from torpedo import CONFIG

from app.common.services.openai.openai_llm_service import OpenAILLMService
from app.common.utils.app_utils import build_openai_conversation_message
from app.main.blueprints.deputy_dev.constants.constants import (
    BitbucketBots,
    ChatTypes,
    MessageTypes,
    MetaStatCollectionTypes,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.models.human_comment_request import (
    HumanCommentRequest,
)
from app.main.blueprints.deputy_dev.services.atlassian.jira.jira_manager import (
    JiraManager,
)
from app.main.blueprints.deputy_dev.services.chat.pre_processors.comment_pre_processer import (
    CommentPreprocessor,
)
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.prompt.chat_prompt_service import (
    ChatPromptService,
)
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.sqs.meta_subscriber import MetaSubscriber
from app.main.blueprints.deputy_dev.services.webhook.chat_webhook import ChatWebhook
from app.main.blueprints.deputy_dev.services.webhook.human_comment_webhook import (
    HumanCommentWebhook,
)
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    set_context_values,
)
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)
from app.main.blueprints.deputy_dev.utils import (
    format_code_blocks,
    get_vcs_auth_handler,
    is_human_comment,
    is_request_from_blocked_repo,
    update_payload_with_jwt_data,
)

config = CONFIG.config


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict, query_params: dict):
        payload = update_payload_with_jwt_data(query_params, payload)
        # some webhooks don't have query params handling for that case
        vcs_type = payload.get("vcs_type") or VCSTypes.bitbucket.value

        comment_payload = await ChatWebhook.parse_payload(payload)
        if not comment_payload:
            return
        logger.info(f"Comment payload: {comment_payload}")
        if is_request_from_blocked_repo(comment_payload.repo.repo_name):
            return
        if (
            is_human_comment(comment_payload.author_info.name, comment_payload.comment.raw)
            and ExperimentService.is_eligible_for_experiment()
        ):
            human_comment_payload = await HumanCommentWebhook.parse_payload(payload)
            await cls.handle_human_comment(human_comment_payload, vcs_type)
        elif comment_payload.author_info.name not in BitbucketBots.list():
            asyncio.ensure_future(cls.handle_chat_request(comment_payload, vcs_type=vcs_type))
        else:
            logger.info(f"Comment rejected due to not falling in supported criteria {comment_payload}")

    @classmethod
    async def handle_chat_request(cls, chat_request: ChatRequest, vcs_type):
        auth_handler = await get_vcs_auth_handler(chat_request.repo.workspace_id, vcs_type)
        repo = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            pr_id=chat_request.repo.pr_id,
            workspace=chat_request.repo.workspace,
            workspace_slug=chat_request.repo.workspace_slug,
            workspace_id=chat_request.repo.workspace_id,
            repo_id=chat_request.repo.repo_id,
            auth_handler=auth_handler,
        )

        comment_service = await CommentFactory.comment(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            pr_id=chat_request.repo.pr_id,
            workspace=chat_request.repo.workspace,
            workspace_slug=chat_request.repo.workspace_slug,
            pr_details=repo.pr_details,
            repo_id=chat_request.repo.repo_id,
            auth_handler=auth_handler,
        )
        # Set Team id in context vars
        workspace_dto = await WorkspaceService.find(scm_workspace_id=chat_request.repo.workspace_id, scm=vcs_type)
        if workspace_dto:
            set_context_values(team_id=workspace_dto.team_id)
        comment = chat_request.comment.raw.lower()
        # we are checking whether the comment starts with any of the tags or not
        add_note = comment.startswith(ChatTypes.SCRIT.value)
        chat_type = await CommentPreprocessor.process_chat(chat_request, repo.pr_model())
        if chat_type == MessageTypes.UNKNOWN.value:
            logger.info(f"Chat processing rejected due to unknown tag with payload : {chat_request}")
        elif chat_type == MessageTypes.CHAT.value:
            comment = chat_request.comment.raw.lower()

            logger.info(f"Processing the comment: {comment} , with payload : {chat_request}")

            diff = await repo.get_pr_diff()
            user_story_description = await JiraManager(issue_id=repo.pr_details.issue_id).get_description_text()
            comment_thread = await comment_service.fetch_comment_thread(chat_request)
            comment_context = {
                "comment_thread": comment_thread,
                "pr_diff": diff,
                "user_story_description": user_story_description,
            }
            await cls.get_chat_comments(comment_context, chat_request, comment_service, add_note)
            logger.info(f"Chat processing completed: {comment} , with payload : {chat_request}")

    @classmethod
    async def get_chat_comments(cls, context, chat_request: ChatRequest, comment_service, add_note: bool = False):
        llm_comment_response = await cls.get_comments_from_llm(
            context, config.get("FEATURE_MODELS").get("PR_CHAT"), chat_request
        )
        logger.info(f"Process chat comment response: {llm_comment_response}")
        await comment_service.process_chat_comment(
            comment=llm_comment_response, chat_request=chat_request, add_note=add_note
        )

    @classmethod
    async def get_comments_from_llm(cls, context: dict, model: str, chat_request: ChatRequest) -> str:
        """
        Makes a call to OpenAI chat completion API with a specific model and conversation messages.

        Parameters:
        - comment_data (str): Comment details that needs to be passed to llm
        - model: GPT model Name defined in config file.

        Returns:
        - formatted_comment (str): Response from the llm server for the comment made on PR.
        """
        client, model_config = (
            OpenAILLMService(),
            CONFIG.config.get("LLM_MODELS").get(model),
        )

        system_prompt, user_message = ChatPromptService.build_chat_prompt(
            pr_diff=context.get("pr_diff"),
            user_story=context.get("user_story_description"),
            comment_thread=context.get("comment_thread"),
            chat_request=chat_request,
        )

        conversation_message = build_openai_conversation_message(
            system_message=system_prompt, user_message=user_message
        )
        response, tokens = await client.get_client_response(
            conversation_message=conversation_message, model=model_config.get("NAME"), response_type="text"
        )
        formatted_comment = format_code_blocks(response.content)
        return formatted_comment

    @classmethod
    async def handle_human_comment(cls, parsed_payload: HumanCommentRequest, vcs_type):
        payload = {
            "payload": parsed_payload.dict(),
            "stats_type": MetaStatCollectionTypes.HUMAN_COMMENT.value,
            "vcs_type": vcs_type,
        }

        await MetaSubscriber(config=config).publish(payload)
