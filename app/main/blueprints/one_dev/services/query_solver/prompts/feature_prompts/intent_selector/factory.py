from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.intent_selector.gemini_2_point_5_flash import (
    Gemini2Point5FlashIntentSelectorPrompt,
)


class IntentSelectorPromptFactory(BaseFeaturePromptFactory):
    intent_selector_prompts = {LLModels.GEMINI_2_POINT_5_FLASH: Gemini2Point5FlashIntentSelectorPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.intent_selector_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
