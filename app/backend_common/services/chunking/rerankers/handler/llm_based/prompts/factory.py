from dataclasses.main import PromptFeatures
from typing import Any, Dict, Type

from feature_prompts.chunk_re_ranking.factory import ChunkReRankingPromptFactory

from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class PromptFeatureFactory:
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.RE_RANKING: ChunkReRankingPromptFactory,
    }

    @classmethod
    def get_prompt(
        cls, prompt_feature: PromptFeatures, model_name: LLModels, init_params: Dict[str, Any]
    ) -> BasePrompt:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(prompt_feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {prompt_feature}")

        prompt_class = feature_prompt_factory.get_prompt(model_name)
        return prompt_class(init_params)
