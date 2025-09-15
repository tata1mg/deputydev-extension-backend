from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.user_query_enhancer.claude_3_point_7_sonnet import (
    Claude3Point7UserQueryEnhancerPrompt,
)


class UserQueryEnhancerPromptFactory(BaseFeaturePromptFactory):
    user_query_enhancer_prompts = {LLModels.CLAUDE_3_POINT_7_SONNET: Claude3Point7UserQueryEnhancerPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.user_query_enhancer_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
