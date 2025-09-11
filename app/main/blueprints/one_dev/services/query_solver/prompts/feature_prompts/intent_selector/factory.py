from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
from pydantic import BaseModel

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.intent_selector.gpt_4_point_1_mini import (
    Gpt4Point1MiniIntentSelectorPrompt,
)


class IntentSelectorPromptFactory(BaseFeaturePromptFactory):
    intent_selector_prompts = {
        LLModels.GPT_4_POINT_1_MINI: Gpt4Point1MiniIntentSelectorPrompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.intent_selector_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class

    @classmethod
    def get_text_format(cls, model_name: LLModels) -> Type[BaseModel]:
        prompt_class = cls.intent_selector_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        if hasattr(prompt_class, "get_text_format"):
            return prompt_class.get_text_format()
        raise ValueError(f"get_text_format method not found for model {model_name}")
