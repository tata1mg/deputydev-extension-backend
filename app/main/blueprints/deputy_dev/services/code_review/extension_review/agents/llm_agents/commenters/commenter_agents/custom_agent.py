from typing import Dict

from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)

from app.main.blueprints.deputy_dev.services.code_review.extension_review.agents.llm_agents.commenters.base_commentor import (
    BaseCommenterAgent,
)


class CustomAgent(BaseCommenterAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.CUSTOM_AGENT_COMMENTS_GENERATION,
    ]
    agent_type = AgentTypes.CUSTOM_COMMENTER_AGENT

    def get_agent_specific_tokens_data(self) -> Dict[str, int]:
        return {
        }
