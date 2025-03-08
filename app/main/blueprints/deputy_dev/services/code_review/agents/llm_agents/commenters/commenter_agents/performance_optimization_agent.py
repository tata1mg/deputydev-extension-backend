from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)

from ..base_commenter import BaseCommenterAgent


class PerformanceOptimizationAgent(BaseCommenterAgent):
    is_dual_pass = True
    prompt_features = [
        PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION_PASS_1,
        PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION_PASS_2,
    ]
    agent_type = AgentTypes.PERFORMANCE_OPTIMIZATION
