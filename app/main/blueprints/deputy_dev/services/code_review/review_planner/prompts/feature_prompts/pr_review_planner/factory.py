from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)

from .claude_3_point_7_sonnet import Claude3Point7ReviewPlannerPrompt


class PRReviewPromptFeatureFactory(BaseFeaturePromptFactory):
    pr_review_planner_prompts = {
        LLModels.CLAUDE_3_POINT_7_SONNET: Claude3Point7ReviewPlannerPrompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.pr_review_planner_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
