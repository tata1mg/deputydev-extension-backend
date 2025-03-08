from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)

from ..base_commenter import BaseCommenterAgent


class ErrorAgent(BaseCommenterAgent):
    is_dual_pass = True
    prompt_features = [PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_1, PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_2]
    agent_type = AgentTypes.ERROR
