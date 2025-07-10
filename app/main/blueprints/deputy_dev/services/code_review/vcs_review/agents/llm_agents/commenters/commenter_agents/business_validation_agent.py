from typing import Dict

from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)

from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.base_commentor import BaseCommenterAgent


class BusinessValidationAgent(BaseCommenterAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_1,
    ]
    agent_type = AgentTypes.BUSINESS_LOGIC_VALIDATION

    async def should_execute(self) -> bool:
        user_story = await self.context_service.get_user_story()
        if user_story:
            return True
        return False

    def get_agent_specific_tokens_data(self) -> Dict[str, int]:
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens[self.agent_id],
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
            TokenTypes.PR_USER_STORY.value: self.context_service.pr_user_story_tokens,
            TokenTypes.PR_CONFLUENCE.value: self.context_service.confluence_doc_data_tokens,
        }
