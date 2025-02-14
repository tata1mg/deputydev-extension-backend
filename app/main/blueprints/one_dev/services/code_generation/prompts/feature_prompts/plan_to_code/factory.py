from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)

from .claude_3_point_5_sonnet import Claude3Point5PlanCodeGenerationPrompt


class PlanCodeGenerationPromptFactory(BaseFeaturePromptFactory):
    plan_to_code_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5PlanCodeGenerationPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.plan_to_code_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
