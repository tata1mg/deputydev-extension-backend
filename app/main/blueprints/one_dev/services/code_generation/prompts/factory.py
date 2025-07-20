from typing import Dict, Type

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.prompts.base_prompt_feature_factory import (
    BasePromptFeatureFactory,
)

from .dataclasses.main import PromptFeatures
from .feature_prompts.chat_filter.factory import ChatRankingPromptFactory


class PromptFeatureFactory(BasePromptFeatureFactory[PromptFeatures]):
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.CHAT_RERANKING: ChatRankingPromptFactory,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels, feature: PromptFeatures) -> Type[BasePrompt]:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {feature}")

        prompt_class = feature_prompt_factory.get_prompt(model_name)
        return prompt_class

    @classmethod
    def get_text_format(cls, model_name: LLModels, feature: PromptFeatures) -> Type[BaseModel]:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {feature}")

        prompt_class = feature_prompt_factory.get_text_format(model_name)
        return prompt_class
