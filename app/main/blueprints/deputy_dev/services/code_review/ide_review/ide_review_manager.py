import textwrap
from typing import Any, Dict, Optional

from deputydev_core.llm_handler.dataclasses.main import PromptCacheConfig
from deputydev_core.utils.app_logger import AppLogger
from sanic.log import logger

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.models.dto.review_agent_status_dto import ReviewAgentStatusDTO
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.agent_factory import AgentFactory
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import AgentRequestItem
from app.main.blueprints.deputy_dev.services.code_review.ide_review.prompts.factory import PromptFeatureFactory
from app.main.blueprints.deputy_dev.services.repository.extension_reviews.repository import ExtensionReviewsRepository
from app.main.blueprints.deputy_dev.services.repository.ide_reviews_comments.repository import IdeCommentRepository
from app.main.blueprints.deputy_dev.services.repository.review_agents_status.repository import (
    ReviewAgentStatusRepository,
)
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
config = CONFIG.config


class IdeReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def review_diff(cls, agent_request: AgentRequestItem) -> Optional[Dict[str, Any]]:
        agent_id = agent_request.agent_id
        review_id = agent_request.review_id
        request_type = agent_request.type.value
        extension_review_dto = await ExtensionReviewsRepository.db_get(filters={"id": review_id}, fetch_one=True)
        user_agent_dto = await UserAgentRepository.db_get(filters={"id": agent_id}, fetch_one=True)
        agent_and_init_params = cls.get_agent_and_init_params_for_review(user_agent_dto)

        context_service = IdeReviewContextService(review_id=review_id)

        llm_handler = LLMServiceManager().create_llm_handler(
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

        agent_result = await agent.run_agent(
            session_id=extension_review_dto.session_id, payload=agent_request.model_dump(mode="python")
        )

        if request_type == "query":
            meta_info = {
                "confidence_score": getattr(user_agent_dto, "confidence_score", None),
                "display_name": user_agent_dto.display_name,
                "agent_name": user_agent_dto.agent_name,
                "custom_prompt": getattr(user_agent_dto, "custom_prompt", None),
                "exclusions": getattr(user_agent_dto, "exclusions", None),
                "inclusions": getattr(user_agent_dto, "inclusions", None),
                "objective": getattr(user_agent_dto, "objective", None),
                "is_custom_agent": getattr(user_agent_dto, "is_custom_agent", False),
            }

            agent_status = ReviewAgentStatusDTO(
                review_id=review_id,
                agent_id=agent_id,
                meta_info=meta_info,
                llm_model=None,  # Will be updated after agent execution
            )
            await ReviewAgentStatusRepository.db_insert(agent_status)

        return cls.format_agent_response(agent_result, agent_id)

    @classmethod
    def format_agent_response(cls, agent_result: AgentRunResult, agent_id: int) -> Optional[Dict[str, Any]]:
        """Format agent result for API response with single response block."""
        agent_result_dict = agent_result.agent_result

        if isinstance(agent_result_dict, dict):
            if agent_result_dict.get("type") == "tool_use_request":
                # Tool use request - frontend needs to process tool
                return {
                    "type": "TOOL_USE_REQUEST",
                    "data": {
                        "tool_name": agent_result_dict["tool_name"],
                        "tool_input": agent_result_dict["tool_input"],
                        "tool_use_id": agent_result_dict["tool_use_id"],
                    },
                    "agent_id": agent_id,
                }
            elif agent_result_dict.get("status") == "success":
                return {
                    "type": "AGENT_COMPLETE",
                    "agent_id": agent_id,
                }
            elif agent_result_dict.get("status") == "error":
                return {
                    "type": "AGENT_FAIL",
                    "data": {"message": agent_result_dict.get("message", "An error occurred")},
                    "agent_id": agent_id,
                }

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
    def _update_bucket_name(agent_result: AgentRunResult) -> None:
        """Update bucket names for agent result comments."""
        comments = agent_result.agent_result["comments"]
        for comment in comments:
            display_name = agent_result.display_name
            comment.bucket = "_".join(display_name.upper().split())

    @classmethod
    async def generate_comment_fix_query(cls, comment_id: int) -> str:
        comment = await IdeCommentRepository.db_get({"id": comment_id}, fetch_one=True)
        if not comment:
            raise ValueError(f"Comment with ID {comment_id} not found")
        query = textwrap.dedent(f"""
            A reviewer has left a comment on file `{comment.file_path}` at line {comment.line_number}.

            Please suggest a code change that addresses the comment accurately while preserving functionality 
            and improving code quality. You have access to the full code, file context, and project structure — 
            use this to guide your response.

            Respond with:
            1. The updated code block only.
            2. A brief explanation (2–3 lines) describing what was changed and why.

            Reviewer Comment:
            {comment.title}
            {comment.comment}
            {comment.corrective_code if comment.corrective_code else ""}
            {comment.rationale if comment.rationale else ""}
        """)
        return query

    async def cancel_review(self, review_id: int) -> Dict[str, str]:
        """Cancel an ongoing review."""
        try:
            review = await ExtensionReviewsRepository.db_get(filters={"id": review_id}, fetch_one=True)
            if not review:
                raise ValueError(f"Review with ID {review_id} not found")

            # Update review status to 'Cancelled'
            await ExtensionReviewsRepository.update_review(review_id, {"review_status": "Cancelled"})
            return {"status": "Cancelled", "message": "Review cancelled successfully"}
        except Exception as e:
            logger.error(f"Error cancelling review {review_id}: {e}")
            raise e
