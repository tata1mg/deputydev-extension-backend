from typing import Type

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.query_summary_generator.gpt_4_point_1_nano import (
    Gpt4Point1NanoQuerySummaryGeneratorPrompt,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt


class QuerySummaryGeneratorPromptFactory(BaseFeaturePromptFactory):
    query_summary_generator_prompts = {
        LLModels.GPT_4_POINT_1_NANO: Gpt4Point1NanoQuerySummaryGeneratorPrompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.query_summary_generator_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
