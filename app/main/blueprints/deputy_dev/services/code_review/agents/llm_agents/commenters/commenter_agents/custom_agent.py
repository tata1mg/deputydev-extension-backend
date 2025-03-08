from typing import Any, Dict, Optional

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)

from ..base_commenter import BaseCommenterAgent


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
    ):
        super().__init__(context_service, is_reflection_enabled, agent_setting, llm_handler, model)
        self.agent_name = custom_commenter_name  # overrides the agent_name value from the base class

    async def required_prompt_variables(
        self, last_pass_result: Dict[str, Optional[str]] = {}
    ) -> Dict[str, Optional[str]]:
        variables = await super().required_prompt_variables(last_pass_result)
        variables["AGENT_NAME"] = self.agent_name
        return variables
