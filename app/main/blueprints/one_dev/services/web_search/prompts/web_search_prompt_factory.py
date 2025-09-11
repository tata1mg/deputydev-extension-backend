from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from app.main.blueprints.one_dev.services.web_search.prompts.gemini_2_point_0_flash import (
    Gemini2Point0FlashWebSearch,
)


class WebSearchPromptFactory(BaseFeaturePromptFactory):
    web_search_prompts = {
        LLModels.GEMINI_2_POINT_0_FLASH: Gemini2Point0FlashWebSearch,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.web_search_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
