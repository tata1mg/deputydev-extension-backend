from typing import Any, Dict, Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.factory import (
    CodeQuerySolverPromptFactory,
)


class PromptFeatureFactory:
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.CODE_QUERY_SOLVER: CodeQuerySolverPromptFactory,
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
