from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from .gpt_o3_mini import GptO3MiniReviewPlannerPrompt


class PRReviewPromptFeatureFactory(BaseFeaturePromptFactory):
    pr_review_planner_prompts = {
        LLModels.GPT_O3_MINI: GptO3MiniReviewPlannerPrompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.pr_review_planner_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
