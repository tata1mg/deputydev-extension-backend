from typing import Any, Dict, Type

from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.prompt.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.common.services.prompt.base_prompt import BasePrompt
from app.common.services.prompt.feature_prompts.chat_filter.factory import (
    ChatRankingPromptFactory,
)
from app.common.services.prompt.feature_prompts.chunk_description_generation.factory import (
    ChunkDescriptionGenerationPromptFactory,
)
from app.common.services.prompt.feature_prompts.chunk_re_ranking.factory import (
    ChunkReRankingPromptFactory,
)
from app.common.services.prompt.feature_prompts.code_generation.factory import (
    CodeGenerationPromptFactory,
)
from app.common.services.prompt.feature_prompts.diff_creation.factory import (
    DiffCreationPromptFactory,
)
from app.common.services.prompt.feature_prompts.docs_generation.factory import (
    DocsGenerationPromptFactory,
)
from app.common.services.prompt.feature_prompts.iterative_code_chat.factory import (
    IterativeCodeChatPromptFactory,
)
from app.common.services.prompt.feature_prompts.plan_to_code.factory import (
    PlanCodeGenerationPromptFactory,
)
from app.common.services.prompt.feature_prompts.task_plan_generation.factory import (
    TaskPlanGenerationPromptFactory,
)
from app.common.services.prompt.feature_prompts.test_case_generation.factory import (
    TestCaseGenerationPromptFactory,
)
from app.common.services.prompt.feature_prompts.test_plan_generation.factory import (
    TestPlanGenerationPromptFactory,
)


class PromptFeatureFactory:
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.CODE_GENERATION: CodeGenerationPromptFactory,
        PromptFeatures.RE_RANKING: ChunkReRankingPromptFactory,
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
