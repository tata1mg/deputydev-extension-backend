from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.common.services.prompt.feature_prompts.code_query_solver.claude_3_point_5_sonnet import (
    Claude3Point5CodeQuerySolverPrompt,
)


class CodeQuerySolverPromptFactory(BaseFeaturePromptFactory):
    code_query_solver_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5CodeQuerySolverPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.code_query_solver_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
