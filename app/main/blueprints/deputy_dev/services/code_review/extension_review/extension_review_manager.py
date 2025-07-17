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
from app.main.blueprints.deputy_dev.services.code_review.extension_review.agents.agent_factory import AgentFactory
from app.main.blueprints.deputy_dev.services.code_review.extension_review.context.extension_context_service import (
    ExtensionContextService,
)

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
config = CONFIG.config


class ExtensionReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def review_diff(cls, payload):
        agent_id = payload.get("agent_id")
        review_id = payload.get("review_id")
        repo_id = payload.get("repo_id")
        session_id = payload.get("session_id")
        user_agent_dto = await UserAgentRepository.db_get(filters={"id": agent_id}, fetch_one=True)
        agent_and_init_params = cls.get_agent_and_init_params_for_review(user_agent_dto)

        context_service = ExtensionContextService(review_id=review_id)

        llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )

        agent = AgentFactory.get_code_review_agent(
            agent_and_init_params=agent_and_init_params,
            context_service=context_service,
            llm_handler=llm_handler,
            user_agent_dto=user_agent_dto,
        )

        agent_result = await agent.run_agent(session_id=session_id, payload=payload)

        return cls._format_agent_response(agent_result, payload.get("agent_id"))

    @classmethod
    def _format_agent_response(cls, agent_result: AgentRunResult, agent_id: int) -> Dict[str, Any]:
        """Format agent result for API response with single response block."""
        agent_result_dict = agent_result.agent_result

        if isinstance(agent_result_dict, dict):
            if agent_result_dict.get("type") == "tool_use_request":
                # Tool use request - frontend needs to process tool
                return {
                    "status": "SUCCESS",
                    "type": "TOOL_USE_REQUEST",
                    "tool_name": agent_result_dict["tool_name"],
                    "tool_input": agent_result_dict["tool_input"],
                    "tool_use_id": agent_result_dict["tool_use_id"],
                    "agent_name": agent_result.agent_name,
                    "agent_type": agent_result.agent_type.value,
                    "tokens_data": agent_result.tokens_data,
                    "model": agent_result.model.value,
                    "display_name": agent_result.display_name,
                    "agent_id": agent_id,
                }
            elif agent_result_dict.get("status") == "success":
                # Review completed successfully
                return {
                    "status": "SUCCESS",
                    "type": "REVIEW_COMPLETE",
                    "message": agent_result_dict.get("message", "Review completed successfully"),
                    "agent_name": agent_result.agent_name,
                    "agent_type": agent_result.agent_type.value,
                    "tokens_data": agent_result.tokens_data,
                    "model": agent_result.model.value,
                    "display_name": agent_result.display_name,
                    "agent_id": agent_id,
                }
            elif agent_result_dict.get("status") == "error":
                # Error occurred
                return {
                    "status": "SUCCESS",
                    "type": "REVIEW_ERROR",
                    "message": agent_result_dict.get("message", "An error occurred"),
                    "agent_name": agent_result.agent_name,
                    "agent_type": agent_result.agent_type.value,
                    "tokens_data": agent_result.tokens_data,
                    "model": agent_result.model.value,
                    "display_name": agent_result.display_name,
                    "agent_id": agent_id,
                }

        # # Generic result or fallback
        # return {
        #     "status": "SUCCESS",
        #     "type": "REVIEW_RESULT",
        #     "result": agent_result_dict,
        #     "agent_name": agent_result.agent_name,
        #     "agent_type": agent_result.agent_type.value,
        #     "tokens_data": agent_result.tokens_data,
        #     "model": agent_result.model.value,
        #     "display_name": agent_result.display_name,
        #     "prompt_tokens_exceeded": agent_result.prompt_tokens_exceeded,
        #     "agent_id": agent_id
        # }

    @classmethod
    def get_agent_and_init_params_for_review(cls, user_agent_dto: UserAgentDTO) -> Optional[AgentAndInitParams]:
        agent_and_init_params = None
        try:
            agent_name = AgentTypes(user_agent_dto.agent_name)
            agent_and_init_params = AgentAndInitParams(agent_type=agent_name)
        except ValueError:
            AppLogger.log_warn(f"Invalid agent name: {user_agent_dto.agent_name}")

        return agent_and_init_params


    @staticmethod
    def _update_bucket_name(agent_result: AgentRunResult):
        """Update bucket names for agent result comments."""
        comments = agent_result.agent_result["comments"]
        for comment in comments:
            display_name = agent_result.display_name
            comment.bucket = "_".join(display_name.upper().split())
