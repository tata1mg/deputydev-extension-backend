from typing import Dict

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


class CodeMaintainabilityAgent(BaseCommenterAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.CODE_MAINTAINABILITY_COMMENTS_GENERATION_PASS_1,
    ]
    agent_type = AgentTypes.CODE_MAINTAINABILITY

    def get_agent_specific_tokens_data(self) -> Dict[str, int]:
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens[self.agent_id],
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
        }
