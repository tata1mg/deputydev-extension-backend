from .dataclasses.main import PromptFeatures
from typing import Any, Dict, Type

from .feature_prompts.chat_filter.factory import ChatRankingPromptFactory
from .feature_prompts.chunk_description_generation.factory import (
    ChunkDescriptionGenerationPromptFactory,
)
from .feature_prompts.code_generation.factory import CodeGenerationPromptFactory
from .feature_prompts.diff_creation.factory import DiffCreationPromptFactory
from .feature_prompts.docs_generation.factory import DocsGenerationPromptFactory
from .feature_prompts.iterative_code_chat.factory import IterativeCodeChatPromptFactory
from .feature_prompts.plan_to_code.factory import PlanCodeGenerationPromptFactory
from .feature_prompts.task_plan_generation.factory import TaskPlanGenerationPromptFactory
from .feature_prompts.test_case_generation.factory import TestCaseGenerationPromptFactory
from .feature_prompts.test_plan_generation.factory import TestPlanGenerationPromptFactory

from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class PromptFeatureFactory:
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.CODE_GENERATION: CodeGenerationPromptFactory,
        PromptFeatures.TEST_GENERATION: TestCaseGenerationPromptFactory,
        PromptFeatures.DOCS_GENERATION: DocsGenerationPromptFactory,
        PromptFeatures.CHUNK_DESCRIPTION_GENERATION: ChunkDescriptionGenerationPromptFactory,
        PromptFeatures.TASK_PLANNER: TaskPlanGenerationPromptFactory,
        PromptFeatures.TEST_PLAN_GENERATION: TestPlanGenerationPromptFactory,
        PromptFeatures.ITERATIVE_CODE_CHAT: IterativeCodeChatPromptFactory,
        PromptFeatures.DIFF_CREATION: DiffCreationPromptFactory,
        PromptFeatures.PLAN_CODE_GENERATION: PlanCodeGenerationPromptFactory,
        PromptFeatures.CHAT_RERANKING: ChatRankingPromptFactory,
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
