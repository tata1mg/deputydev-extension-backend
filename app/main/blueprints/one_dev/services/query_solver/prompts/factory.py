from typing import Dict, Type

from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.chat_filter.factory import (
    ChatRankingPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.factory import (
    CodeQuerySolverPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.factory import (
    InlineEditorPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.intent_selector.factory import (
    IntentSelectorPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.query_summary_generator.factory import (
    QuerySummaryGeneratorPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.session_summary_generator.factory import (
    SessionSummaryGeneratorPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.terminal_command_editor.factory import (
    TerminalCommandEditorPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.user_query_enhancer.factory import (
    UserQueryEnhancerPromptFactory,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
from deputydev_core.llm_handler.prompts.base_prompt_feature_factory import BasePromptFeatureFactory


class PromptFeatureFactory(BasePromptFeatureFactory[PromptFeatures]):
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.SESSION_SUMMARY_GENERATOR: SessionSummaryGeneratorPromptFactory,
        PromptFeatures.INLINE_EDITOR: InlineEditorPromptFactory,
        PromptFeatures.TERMINAL_COMMAND_EDITOR: TerminalCommandEditorPromptFactory,
        PromptFeatures.USER_QUERY_ENHANCER: UserQueryEnhancerPromptFactory,
        PromptFeatures.INTENT_SELECTOR: IntentSelectorPromptFactory,
        PromptFeatures.CODE_QUERY_SOLVER: CodeQuerySolverPromptFactory,
        PromptFeatures.QUERY_SUMMARY_GENERATOR: QuerySummaryGeneratorPromptFactory,
        PromptFeatures.CHAT_RERANKING: ChatRankingPromptFactory,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels, feature: PromptFeatures) -> Type[BasePrompt]:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {feature}")

        prompt_class = feature_prompt_factory.get_prompt(model_name)
        return prompt_class
