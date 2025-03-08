from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)

from ..base_commenter import BaseCommenterAgent


class BusinessValidationAgent(BaseCommenterAgent):
    is_dual_pass = True
    prompt_features = [
        PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_1,
        PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_2,
    ]
    agent_type = AgentTypes.BUSINESS_LOGIC_VALIDATION

    async def should_execute(self) -> bool:
        user_story = await self.context_service.get_user_story()
        if user_story:
            return True
        return False
