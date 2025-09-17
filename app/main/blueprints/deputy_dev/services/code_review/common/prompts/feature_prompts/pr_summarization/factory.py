from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from .gpt_4_point_1 import GPT4Point1PRSummarizationPrompt


class PRSummarizationPromptFactory(BaseFeaturePromptFactory):
    prompts = {LLModels.GPT_4_POINT_1: GPT4Point1PRSummarizationPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
