from typing import Any, Dict, Optional

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.constants.constants import PRStatus
from app.main.blueprints.deputy_dev.constants.constants import FeatureFlows, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)


class PRSummarizerAgent(BaseCodeReviewAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.PR_SUMMARIZATION,
    ]
    agent_type = AgentTypes.PR_SUMMARY

    def __init__(
        self,
        context_service: ContextService,
        is_reflection_enabled: bool,
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
    ) -> None:
        super().__init__(context_service, is_reflection_enabled, llm_handler, model)
        self.agent_setting = SettingService.helper.agent_setting_by_name(self.agent_name)
        self.agent_id: str = SettingService.helper.summary_agent_id()

    def agent_relevant_chunk(self, relevant_chunks: Dict[str, Any]) -> str:
        relevant_chunks_indexes = relevant_chunks["comment_validation_relevant_chunks_mapping"]
        chunks = [relevant_chunks["relevant_chunks"][index] for index in relevant_chunks_indexes]
        return render_snippet_array(chunks)

    async def required_prompt_variables(
        self, last_pass_result: Dict[str, Optional[str]] = {}
    ) -> Dict[str, Optional[str]]:
        return {
            "PULL_REQUEST_TITLE": self.context_service.get_pr_title(),
            "PR_DIFF_WITHOUT_LINE_NUMBER": await self.context_service.get_pr_diff(),
        }

    def get_agent_specific_tokens_data(self) -> Dict[str, Any]:
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: (
                self.context_service.pr_diff_tokens[self.agent_id] if self.context_service.pr_diff_tokens else 0
            ),
        }

    async def should_execute(self) -> bool:
        feature_flow = FeatureFlows(get_context_value("feature_flow"))
        pr_status = PRStatus(self.context_service.get_pr_status())

        if feature_flow == FeatureFlows.INCREMENTAL_SUMMARY:
            return True

        # Summary agent is disabled for closed PRs and Incremental review PRs
        if feature_flow == FeatureFlows.INCREMENTAL_CODE_REVIEW or (
            feature_flow == FeatureFlows.INITIAL_CODE_REVIEW and pr_status in [PRStatus.MERGED, PRStatus.DECLINED]
        ):
            return False

        return True
