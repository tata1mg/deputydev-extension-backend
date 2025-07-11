from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import set_context_values
from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG

from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.workspace.context_var import identifier
from app.backend_common.utils.log_time import log_time
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_SIZE_TOO_BIG_MESSAGE,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.base_pr_review_manager import (
    BasePRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.multi_agent_pr_review_manager import (
    MultiAgentPRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.common.post_processors.pr_review_post_processor import (
    PRReviewPostProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.pre_processors.pr_review_pre_processor import (
    PRReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.comment.affirmation_comment_service import (
    AffirmationService,
)

from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import ContextService
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.factory import (
    PromptFeatureFactory,
)
from app.backend_common.services.llm.dataclasses.main import PromptCacheConfig
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
config = CONFIG.config


class PRReviewManager1(BasePRReviewManager):
    """Manager for processing Pull Request reviews."""


    @classmethod
    async def review_diff(
            cls,
            payload
    ):
        agent_id = payload.get("agent_id")
        user_agent_dto = UserAgentRepository.db_get(filters={"agent_id": agent_id}, fetch_one=True)
        agents_and_init_params = cls.get_agent_and_init_params_for_review(user_agent_dto)



        # non_error_results, is_large_pr = await MultiAgentPRReviewManager(
        #     repo_service, pr_service, pr_diff_handler, session_id, prompt_version
        # ).get_code_review_comments(valid_agents_and_init_params)

        # return non_error_results, is_large_pr


    @classmethod
    def get_agent_and_init_params_for_review(
            cls, user_agent_dto: UserAgentDTO
    ) -> Optional[AgentAndInitParams]:

        agent_and_init_params = None
        try:
            agent_name = AgentTypes(user_agent_dto.agent_name)
            agent_and_init_params = AgentAndInitParams(agent_type=agent_name)
        except ValueError:
            AppLogger.log_warn(f"Invalid agent name: {user_agent_dto.agent_name}")

        return agent_and_init_params

    # @classmethod
    # async def post_process_review_results(
    #         cls,
    #         agent_results: List[AgentRunResult],
    #         is_large_pr: bool,
    #         repo_service: BaseRepo,
    #         pr_service: BasePR,
    #         comment_service: BaseComment,
    #         pr_diff_handler: PRDiffHandler,
    #         session_id: int,
    #         execution_start_time: datetime,
    #         data: Dict[str, Any],
    #         affirmation_service,
    #         pr_dto,
    # ) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any], Dict[str, Any], bool]:
    #     """Post-process agent results to generate final comments and metadata.
    #
    #     Args:
    #         agent_results: List of agent run results
    #         is_large_pr: Whether this is a large PR
    #         repo_service: Repository service
    #         pr_service: PR service
    #         comment_service: Comment service
    #         pr_diff_handler: PR diff handler
    #         session_id: Session ID for the review
    #
    #     Returns:
    #         Tuple of (comments, tokens_data, meta_info_to_save, is_large_pr)
    #     """
    #     agents_tokens = {}
    #     filtered_comments = None
    #     agent_results_dict: Dict[str, AgentRunResult] = {}
    #     blending_agent_results: Dict[str, AgentRunResult] = {}
    #
    #     # Handle large PR case
    #     if is_large_pr:
    #         agents_tokens = await pr_diff_handler.get_pr_diff_token_count()
    #         return None, agents_tokens, {
    #             "issue_id": None,
    #             "confluence_doc_id": None,
    #         }, is_large_pr
    #
    #     # Process agent results
    #     for agent_result in agent_results:
    #         if agent_result.agent_result is not None:
    #             if agent_result.agent_type != AgentTypes.PR_SUMMARY:
    #                 cls._update_bucket_name(agent_result)
    #             agent_results_dict[agent_result.agent_name] = agent_result
    #
    #     # Extract PR summary
    #     pr_summary_result = agent_results_dict.pop(AgentTypes.PR_SUMMARY.value, None)
    #     pr_summary = pr_summary_result.agent_result if pr_summary_result else None
    #     pr_summary_tokens = pr_summary_result.tokens_data if pr_summary_result else {}
    #
    #     # Set up context service and LLM handler for comment blending
    #     context_service = ContextService(repo_service, pr_service, pr_diff_handler=pr_diff_handler)
    #
    #     llm_handler = LLMHandler(
    #         prompt_factory=PromptFeatureFactory,
    #         prompt_features=PromptFeatures,
    #         cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
    #     )
    #
    #     # Filter comments using blending engine
    #     if agent_results_dict:
    #         filtered_comments, blending_agent_results = await CommentBlendingEngine(
    #             agent_results_dict, context_service, llm_handler, session_id
    #         ).blend_comments()
    #
    #     # Update agent results with blending results
    #     agent_results_dict.update(blending_agent_results)
    #
    #     # Populate token information
    #     agents_tokens.update(pr_summary_tokens)
    #     for agent, agent_run_results in agent_results_dict.items():
    #         agents_tokens.update(agent_run_results.tokens_data)
    #
    #     # Format final response
    #     formatted_summary = ""
    #     if pr_summary:
    #         from app.backend_common.utils.formatting import format_summary_with_metadata
    #         loc = await pr_service.get_loc_changed_count()
    #         formatted_summary = format_summary_with_metadata(
    #             summary=pr_summary, loc=loc, commit_id=pr_service.pr_model().commit_id()
    #         )
    #
    #     final_comments = (
    #         [comment.model_dump(mode="json") for comment in filtered_comments]
    #         if filtered_comments else None
    #     )
    #
    #     # We will only post summary for first PR review request
    #     if pr_summary:
    #         await pr_service.update_pr_description(formatted_summary)
    #
    #     if is_large_pr:
    #         await comment_service.create_pr_comment(
    #             comment=PR_SIZE_TOO_BIG_MESSAGE, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
    #         )
    #     elif cls.check_no_pr_comments(final_comments):
    #         await comment_service.create_pr_comment("LGTM!!", config.get("FEATURE_MODELS").get("PR_REVIEW"))
    #     else:
    #         await comment_service.post_bots_comments(final_comments)
    #
    #     meta_info_to_save = {
    #         "issue_id": context_service.issue_id,
    #         "confluence_doc_id": context_service.confluence_id,
    #         "execution_start_time": execution_start_time,
    #         "pr_review_start_time": data.get("pr_review_start_time")
    #     }
    #     await PRReviewPostProcessor(
    #         pr_service=pr_service,
    #         comment_service=comment_service,
    #         affirmation_service=affirmation_service,
    #     ).post_process_pr(pr_dto, final_comments, agents_tokens, is_large_pr, meta_info_to_save)


    @staticmethod
    def _update_bucket_name(agent_result: AgentRunResult):
        """Update bucket names for agent result comments."""
        comments = agent_result.agent_result["comments"]
        for comment in comments:
            display_name = agent_result.display_name
            comment.bucket = "_".join(display_name.upper().split())
