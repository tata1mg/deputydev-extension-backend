from typing import Dict, Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.prompts.base_prompt_feature_factory import (
    BasePromptFeatureFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.factory import (
    CodeQuerySolverPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.factory import (
    InlineEditorPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.user_query_enhancer.factory import UserQueryEnhancerPromptFactory
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.session_summary_generator.factory import (
    SessionSummaryGeneratorPromptFactory,
)


class PromptFeatureFactory(BasePromptFeatureFactory[PromptFeatures]):
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.CODE_QUERY_SOLVER: CodeQuerySolverPromptFactory,
        PromptFeatures.SESSION_SUMMARY_GENERATOR: SessionSummaryGeneratorPromptFactory,
        PromptFeatures.INLINE_EDITOR: InlineEditorPromptFactory,
        PromptFeatures.USER_QUERY_ENHANCER: UserQueryEnhancerPromptFactory,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels, feature: PromptFeatures) -> Type[BasePrompt]:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {feature}")

        prompt_class = feature_prompt_factory.get_prompt(model_name)
        return prompt_class
