from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import set_context_values
from pydantic import ValidationError
from sanic.log import logger

from app.backend_common.services.llm.dataclasses.main import PromptCacheConfig
from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.workspace.context_var import identifier
from app.backend_common.utils.log_time import log_time
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_SIZE_TOO_BIG_MESSAGE,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.comment_blending_engine import (
    CommentBlendingEngine,
)
from app.main.blueprints.deputy_dev.services.code_review.common.post_processors.pr_review_post_processor import (
    PRReviewPostProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.factory import (
    PromptFeatureFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.base_pr_review_manager import (
    BasePRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import ContextService
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.multi_agent_pr_review_manager import (
    MultiAgentPRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.pre_processors.pr_review_pre_processor import (
    PRReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.comment.affirmation_comment_service import (
    AffirmationService,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
config = CONFIG.config


class PRReviewManager(BasePRReviewManager):
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        # Although we will be receiving validated payload, this is just an edge case handling, where
        # someone was able to manually push invalid message to SQS, we will check the incoming SQS message
        # if it's fine then we start the PR review process, otherwise we log the invalid payload and purge the message
        try:
            CodeReviewRequest(**data)
            logger.info("Received MessageQueue Message: {}".format(data))
            set_context_values(repo_origin=data.get("repo_origin"))
            if not data.get("is_review_enabled"):
                return await PRReviewManager.handle_non_reviewable_request(data)
            await cls.process_pr_review(data=data)
            AppLogger.log_info("Completed PR review: ")
        except ValidationError as e:
            AppLogger.log_error(f"Received Invalid Message From MessageQueue - {data}: {e}")
        except Exception as e:
            AppLogger.log_error(f"Unable to review PR: {e}")
            raise

    @classmethod
    async def handle_non_reviewable_request(cls, data: Dict[str, Any]) -> None:
        """Handle non-reviewable requests by creating appropriate notifications and DB entries.

        Args:
            data (Dict[str, Any]): Dictionary containing necessary data for processing the request.
        """
        try:
            repo_service, pr_service, comment_service = await cls.initialise_services(data)
            pr_diff_handler = PRDiffHandler(pr_service)
            affirmation_service = AffirmationService(data, comment_service)

            pre_processor = PRReviewPreProcessor(
                repo_service=repo_service,
                pr_service=pr_service,
                comment_service=comment_service,
                affirmation_service=affirmation_service,
                pr_diff_handler=pr_diff_handler,
            )
            await pre_processor.handle_non_reviewable_request(data)

        except Exception as ex:
            AppLogger.log_error(f"Error while processing non-reviewable request: {ex}")
            raise ex

    @staticmethod
    def set_identifier(value: str) -> None:
        """Set repo_name or any other value to the contextvar identifier

        Args:
            value (str): value to set for the identifier
        """
        identifier.set(value)

    @classmethod
    @log_time
    async def process_pr_review(cls, data: Dict[str, Any]) -> None:
        """Process a Pull Request review asynchronously.

        Args:
            data (Dict[str, Any]): Dictionary containing necessary data for processing the review.
                Expected keys: 'repo_name', 'branch', 'vcs_type', 'pr_id', 'confidence_score'.
        Returns:
            None
        """
        repo_service, pr_service, comment_service = await cls.initialise_services(data)
        pr_diff_handler = PRDiffHandler(pr_service)
        affirmation_service = AffirmationService(data, comment_service)
        pre_processor = None

        try:
            execution_start_time = datetime.now()
            pre_processor = PRReviewPreProcessor(
                repo_service=repo_service,
                pr_service=pr_service,
                comment_service=comment_service,
                affirmation_service=affirmation_service,
                pr_diff_handler=pr_diff_handler,
            )
            await pre_processor.pre_process_pr()

            if not pre_processor.is_reviewable_request:
                return
            set_context_values(session_id=pre_processor.session_id)
            if not pre_processor.session_id:
                AppLogger.log_error("Session id not found for PR review")
                raise Exception("Session id not found for PR review")

            agent_results, is_large_pr = await cls.review_pr(
                pre_processor.session_id,
                repo_service,
                comment_service,
                pr_service,
                data["prompt_version"],
                pr_diff_handler,
            )
            await cls.post_process_review_results(
                agent_results,
                is_large_pr,
                repo_service,
                pr_service,
                comment_service,
                pr_diff_handler,
                pre_processor.session_id,
                execution_start_time,
                data,
                affirmation_service,
                pre_processor.pr_dto,
            )

        except Exception as ex:
            # if PR is inserted in db then only we will update status
            if pre_processor and pre_processor.pr_dto:
                await PRService.db_update(
                    payload={
                        "review_status": PrStatusTypes.FAILED.value,
                    },
                    filters={"id": pre_processor.pr_dto.id},
                )
            AppLogger.log_error("Error while processing PR review")
            raise ex
        finally:
            repo_service.delete_local_repo()

    @classmethod
    def check_no_pr_comments(cls, llm_response: List) -> bool:
        return not llm_response

    @classmethod
    async def review_pr(
        cls,
        session_id: int,
        repo_service: BaseRepo,
        comment_service: BaseComment,
        pr_service: BasePR,
        prompt_version: str,
        pr_diff_handler: PRDiffHandler,
    ) -> Tuple[Optional[List[Dict[str, Any]]], str, Dict[str, Any], Dict[str, Any], bool]:
        valid_agents_and_init_params = cls.get_valid_agents_and_init_params_for_review()
        non_error_results, is_large_pr = await MultiAgentPRReviewManager(
            repo_service, pr_service, pr_diff_handler, session_id, prompt_version
        ).get_code_review_comments(valid_agents_and_init_params)

        return non_error_results, is_large_pr

    @classmethod
    def get_valid_agents_and_init_params_for_review(
        cls,
    ) -> List[AgentAndInitParams]:
        valid_agents: List[AgentAndInitParams] = []

        # add predefined and custom code commenter agents
        code_review_agent_rules = SettingService.helper.global_code_review_agent_rules()
        if code_review_agent_rules.get("enable"):
            agent_settings = SettingService.helper.agents_settings()
            for agent_name, agent_setting in agent_settings.items():
                if agent_setting["enable"]:
                    if agent_setting["is_custom_agent"]:
                        valid_agents.append(
                            AgentAndInitParams(
                                agent_type=AgentTypes.CUSTOM_COMMENTER_AGENT,
                                init_params={"custom_commenter_name": agent_name},
                            )
                        )
                    else:
                        try:
                            agent_name = AgentTypes(agent_name)
                            valid_agents.append(AgentAndInitParams(agent_type=agent_name))
                        except ValueError:
                            AppLogger.log_warn(f"Invalid agent name: {agent_name}")

        # add code summarization agent
        summary_agent_setting = SettingService.helper.summary_agent_setting()
        if summary_agent_setting.get("enable"):
            valid_agents.append(AgentAndInitParams(agent_type=AgentTypes.PR_SUMMARY))

        return valid_agents

    @classmethod
    async def post_process_review_results(  # noqa: C901
        cls,
        agent_results: List[AgentRunResult],
        is_large_pr: bool,
        repo_service: BaseRepo,
        pr_service: BasePR,
        comment_service: BaseComment,
        pr_diff_handler: PRDiffHandler,
        session_id: int,
        execution_start_time: datetime,
        data: Dict[str, Any],
        affirmation_service: AffirmationService,
        pr_dto: PullRequestDTO,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any], Dict[str, Any], bool]:
        """Post-process agent results to generate final comments and metadata.

        Args:
            agent_results: List of agent run results
            is_large_pr: Whether this is a large PR
            repo_service: Repository service
            pr_service: PR service
            comment_service: Comment service
            pr_diff_handler: PR diff handler
            session_id: Session ID for the review

        Returns:
            Tuple of (comments, tokens_data, meta_info_to_save, is_large_pr)
        """
        agents_tokens = {}
        filtered_comments = None
        agent_results_dict: Dict[str, AgentRunResult] = {}
        blending_agent_results: Dict[str, AgentRunResult] = {}

        # Handle large PR case
        if is_large_pr:
            agents_tokens = await pr_diff_handler.get_pr_diff_token_count()
            return (
                None,
                agents_tokens,
                {
                    "issue_id": None,
                    "confluence_doc_id": None,
                },
                is_large_pr,
            )

        # Process agent results
        for agent_result in agent_results:
            if agent_result.agent_result is not None:
                if agent_result.agent_type != AgentTypes.PR_SUMMARY:
                    cls._update_bucket_name(agent_result)
                agent_results_dict[agent_result.agent_name] = agent_result

        # Extract PR summary
        pr_summary_result = agent_results_dict.pop(AgentTypes.PR_SUMMARY.value, None)
        pr_summary = pr_summary_result.agent_result if pr_summary_result else None
        pr_summary_tokens = pr_summary_result.tokens_data if pr_summary_result else {}

        # Set up context service and LLM handler for comment blending
        context_service = ContextService(repo_service, pr_service, pr_diff_handler=pr_diff_handler)

        llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )

        # Filter comments using blending engine
        if agent_results_dict:
            filtered_comments, blending_agent_results = await CommentBlendingEngine(
                agent_results_dict, context_service, llm_handler, session_id
            ).blend_comments()

        # Update agent results with blending results
        agent_results_dict.update(blending_agent_results)

        # Populate token information
        agents_tokens.update(pr_summary_tokens)
        for agent, agent_run_results in agent_results_dict.items():
            agents_tokens.update(agent_run_results.tokens_data)

        # Format final response
        formatted_summary = ""
        if pr_summary:
            from app.backend_common.utils.formatting import format_summary_with_metadata

            loc = await pr_service.get_loc_changed_count()
            formatted_summary = format_summary_with_metadata(
                summary=pr_summary, loc=loc, commit_id=pr_service.pr_model().commit_id()
            )

        final_comments = (
            [comment.model_dump(mode="json") for comment in filtered_comments] if filtered_comments else None
        )

        # We will only post summary for first PR review request
        if pr_summary:
            await pr_service.update_pr_description(formatted_summary)

        if is_large_pr:
            await comment_service.create_pr_comment(
                comment=PR_SIZE_TOO_BIG_MESSAGE, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )
        elif cls.check_no_pr_comments(final_comments):
            await comment_service.create_pr_comment("LGTM!!", config.get("FEATURE_MODELS").get("PR_REVIEW"))
        else:
            await comment_service.post_bots_comments(final_comments)

        meta_info_to_save = {
            "issue_id": context_service.issue_id,
            "confluence_doc_id": context_service.confluence_id,
            "execution_start_time": execution_start_time,
            "pr_review_start_time": data.get("pr_review_start_time"),
        }
        await PRReviewPostProcessor(
            pr_service=pr_service,
            comment_service=comment_service,
            affirmation_service=affirmation_service,
        ).post_process_pr(pr_dto, final_comments, agents_tokens, is_large_pr, meta_info_to_save)

    @staticmethod
    def _update_bucket_name(agent_result: AgentRunResult) -> None:
        """Update bucket names for agent result comments."""
        comments = agent_result.agent_result["comments"]
        for comment in comments:
            display_name = agent_result.display_name
            comment.bucket = "_".join(display_name.upper().split())
