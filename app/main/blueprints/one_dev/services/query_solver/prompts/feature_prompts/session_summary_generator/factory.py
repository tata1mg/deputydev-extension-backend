from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.session_summary_generator.gemini_2_point_5_flash import (
    Gemini2Point5FlashSessionSummaryGeneratorPrompt,
)


class SessionSummaryGeneratorPromptFactory(BaseFeaturePromptFactory):
    session_summary_generator_prompts = {
        LLModels.GEMINI_2_POINT_5_FLASH: Gemini2Point5FlashSessionSummaryGeneratorPrompt
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.session_summary_generator_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
