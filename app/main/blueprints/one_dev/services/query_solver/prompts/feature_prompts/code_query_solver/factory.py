from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_3_point_5_sonnet import (
    Claude3Point5CodeQuerySolverPrompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_pro import (
    Gemini2Point5Pro,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_4_point_1 import (
    Gpt4Point1Prompt,
)


class CodeQuerySolverPromptFactory(BaseFeaturePromptFactory):
    code_query_solver_prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5CodeQuerySolverPrompt,
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5Pro,
        LLModels.GPT_4_POINT_1: Gpt4Point1Prompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.code_query_solver_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
