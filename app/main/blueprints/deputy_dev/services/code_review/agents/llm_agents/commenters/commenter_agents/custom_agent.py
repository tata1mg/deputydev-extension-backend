from typing import Any, Dict, Optional

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
        agent_setting: Dict[str, Any],
    ):
        super().__init__(context_service, is_reflection_enabled, agent_setting)
        self.agent_name = custom_commenter_name  # overrides the agent_name value from the base class

    async def required_prompt_variables(self, comments: Optional[str] = None) -> Dict[str, Optional[str]]:
        variables = await super().required_prompt_variables(comments)
        variables["AGENT_NAME"] = self.agent_name
        return variables
