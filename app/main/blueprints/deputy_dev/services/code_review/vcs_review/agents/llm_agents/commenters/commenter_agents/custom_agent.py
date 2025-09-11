from typing import Any, Dict, Optional

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.base_commentor import (
    BaseCommenterAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)


class CustomAgent(BaseCommenterAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.CUSTOM_AGENT_COMMENTS_GENERATION,
    ]
    agent_type = AgentTypes.CUSTOM_COMMENTER_AGENT

    def __init__(
        self,
        context_service: ContextService,
        is_reflection_enabled: bool,
        custom_commenter_name: str,
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
        agent_setting: Dict[str, Any],
    ) -> None:
        super().__init__(context_service, is_reflection_enabled, agent_setting, llm_handler, model)
        self.agent_name = custom_commenter_name  # overrides the agent_name value from the base class

    async def required_prompt_variables(self, last_pass_result: Optional[Any] = None) -> Dict[str, Optional[str]]:
        variables = await super().required_prompt_variables(last_pass_result)
        variables["AGENT_NAME"] = self.agent_name
        return variables

    def get_agent_specific_tokens_data(self) -> Dict[str, int]:
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens[self.agent_id],
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
        }
