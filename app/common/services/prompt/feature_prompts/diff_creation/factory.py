from app.common.constants.constants import LLModels
from app.common.services.prompt.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.common.services.prompt.feature_prompts.diff_creation.claude_3_point_5_sonnet import (
    Claude3Point5DiffCreationPrompt,
)


class DiffCreationPromptFactory(BaseFeaturePromptFactory):
    diff_creation_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5DiffCreationPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.diff_creation_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
