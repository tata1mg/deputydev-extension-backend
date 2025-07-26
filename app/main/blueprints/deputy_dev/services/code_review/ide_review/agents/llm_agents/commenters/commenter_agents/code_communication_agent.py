from typing import Dict

from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)

from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor import (
    BaseCommenterAgent,
)


class CodeCommunicationAgent(BaseCommenterAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION,
    ]
    agent_type = AgentTypes.CODE_COMMUNICATION

    def get_agent_specific_tokens_data(self) -> Dict[str, int]:
        return {
            # TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens[self.agent_id],
        }
