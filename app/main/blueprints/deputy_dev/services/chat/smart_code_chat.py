from sanic.log import logger
from torpedo import CONFIG

from app.backend_common.repository.repo.repo_service import RepoService
from app.backend_common.services.openai.openai_llm_service import OpenAILLMService
from app.backend_common.services.pr.pr_factory import PRFactory
from app.backend_common.services.repo.repo_factory import RepoFactory
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.backend_common.utils.app_utils import build_openai_conversation_message
from app.backend_common.utils.formatting import format_code_blocks
from app.common.constants.constants import VCSTypes
from app.common.utils.context_vars import set_context_values
from app.main.blueprints.deputy_dev.constants.constants import (
    CHAT_ERRORS,
    BitbucketBots,
    ChatTypes,
    MessageTypes,
    MetaStatCollectionTypes,
)
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
from app.main.blueprints.deputy_dev.services.code_review.code_review_trigger import (
    CodeReviewTrigger,
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
from app.main.blueprints.deputy_dev.services.sqs.meta_subscriber import MetaSubscriber
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_trigger import (
    StatsCollectionTrigger,
)
from app.main.blueprints.deputy_dev.services.webhook.chat_webhook import ChatWebhook
from app.main.blueprints.deputy_dev.services.webhook.human_comment_webhook import (
    HumanCommentWebhook,
)
from app.main.blueprints.deputy_dev.services.workspace.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.utils import (
    get_vcs_auth_handler,
    is_human_comment,
    is_request_from_blocked_repo,
    update_payload_with_jwt_data,
)

# from app.main.blueprints.one_dev.services.webhook_handlers.suggestion_code_generation_manager import (
#     SuggestionCodeGenerationManager,
# )

config = CONFIG.config


class SmartCodeChatManager:
    @classmethod
    async def chat(cls, payload: dict, query_params: dict):
        logger.info(f"Comment payload: {payload}")
        logger.info(f"comment query params {query_params}")
        payload = update_payload_with_jwt_data(query_params, payload)
        # some webhooks don't have query params handling for that case
        vcs_type = payload.get("vcs_type") or VCSTypes.bitbucket.value

        raw_comment = ChatWebhook.get_raw_comment(payload)

        if raw_comment and raw_comment.strip().lower() == "#review":
            await CodeReviewTrigger.perform_review(payload, query_params)
            return

        comment_payload = await ChatWebhook.parse_payload(payload)
        if not comment_payload:
            return
        logger.info(f"Comment payload: {comment_payload}")
        if is_request_from_blocked_repo(comment_payload.repo.repo_name):
            return

        # if comment_payload.comment.raw.strip().startswith("#suggestion"):
        #     asyncio.ensure_future(SuggestionCodeGenerationManager.process_suggestion(comment_payload, vcs_type))
        #     return

        if (
            is_human_comment(comment_payload.author_info.name, comment_payload.comment.raw)
            and ExperimentService.is_eligible_for_experiment()
        ):
            human_comment_payload = await HumanCommentWebhook.parse_payload(payload)
            await cls.handle_human_comment(human_comment_payload, vcs_type)
        elif comment_payload.author_info.name not in BitbucketBots.list():
            await cls.handle_chat_request(comment_payload, vcs_type=vcs_type)
        else:
            logger.info(f"Comment rejected due to not falling in supported criteria {comment_payload}")

    @classmethod
    async def handle_chat_request(cls, chat_request: ChatRequest, vcs_type):
        auth_handler = await get_vcs_auth_handler(chat_request.repo.workspace_id, vcs_type)

        repo = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            workspace=chat_request.repo.repo_name,
            workspace_slug=chat_request.repo.workspace_slug,
            workspace_id=chat_request.repo.workspace_id,
            auth_handler=auth_handler,
        )

        pr = await PRFactory.pr(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            pr_id=chat_request.repo.pr_id,
            workspace=chat_request.repo.workspace,
            workspace_slug=chat_request.repo.workspace_slug,
            workspace_id=chat_request.repo.workspace_id,
            auth_handler=auth_handler,
            fetch_pr_details=True,
            repo_service=repo,
        )

        comment_service = await CommentFactory.initialize(
            vcs_type=vcs_type,
            repo_name=chat_request.repo.repo_name,
            pr_id=chat_request.repo.pr_id,
            workspace=chat_request.repo.workspace,
            workspace_slug=chat_request.repo.workspace_slug,
            pr_details=pr.pr_details,
            repo_id=chat_request.repo.repo_id,
            auth_handler=auth_handler,
        )
        # Set Team id in context vars
        workspace_dto = await WorkspaceService.find(scm_workspace_id=chat_request.repo.workspace_id, scm=vcs_type)
        team_id = None
        if workspace_dto:
            set_context_values(team_id=workspace_dto.team_id)
            team_id = workspace_dto.team_id

        # This creates repo entry in db if not exist.
        await RepoService.find_or_create_with_workspace_id(
            scm_workspace_id=chat_request.repo.workspace_id, pr_model=pr.pr_model()
        )
        setting = await SettingService(repo, team_id).build()
        if not setting["chat"]["enable"]:
            await comment_service.create_comment_on_parent(
                "Chat feature is disable for this repo.", chat_request.comment.id, ""
            )
            return
        comment = chat_request.comment.raw.lower()
        # we are checking whether the comment starts with any of the tags or not
        add_note = comment.startswith(ChatTypes.SCRIT.value)
        chat_type = await CommentPreprocessor.process_chat(chat_request, pr.pr_model())
        if chat_type == MessageTypes.UNKNOWN.value:
            logger.info(f"Chat processing rejected due to unknown tag with payload : {chat_request}")
        elif chat_type == MessageTypes.CHAT.value:
            comment = chat_request.comment.raw.lower()

            logger.info(f"Processing the comment: {comment} , with payload : {chat_request}")

            diff = await pr.get_effective_pr_diff("chat")
            user_story_description = await JiraManager(issue_id=pr.pr_details.issue_id).get_description_text()
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
        comment = cls.append_settings_error(llm_comment_response)
        logger.info(f"Process chat comment response: {comment}")
        await comment_service.process_chat_comment(comment=comment, chat_request=chat_request, add_note=add_note)

    @classmethod
    def append_settings_error(cls, comment):
        error_message = SettingService.fetch_setting_errors(CHAT_ERRORS)
        if error_message:
            comment = f"**Warning**: {error_message}\n\n{comment}"
        return comment

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
        if await StatsCollectionTrigger().is_pr_created_post_onboarding(parsed_payload, vcs_type):
            payload = {
                "payload": parsed_payload.dict(),
                "stats_type": MetaStatCollectionTypes.HUMAN_COMMENT.value,
                "vcs_type": vcs_type,
            }
            await MetaSubscriber(config=config).publish(payload)
