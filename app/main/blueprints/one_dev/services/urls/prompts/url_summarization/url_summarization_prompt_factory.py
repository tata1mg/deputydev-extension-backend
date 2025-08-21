from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt

from .gemini_2_point_5_pro import Gemini2Point5ProUrlSummaryGenerator


class UrlSummarizationPromptFactory(BaseFeaturePromptFactory):
    url_summarization_prompts = {
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5ProUrlSummaryGenerator,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.url_summarization_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
