from app.common.constants.constants import LLModels
from app.common.services.prompt.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.common.services.prompt.feature_prompts.plan_code_generation.claude_3_point_5_sonnet import (
    Claude3Point5PlanCodeGenerationPrompt,
)


class PlanCodeGenerationPromptFactory(BaseFeaturePromptFactory):
    plan_code_generation_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5PlanCodeGenerationPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.plan_code_generation_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
