from typing import Dict, Type

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_3_point_5_sonnet_handler import (
    Claude3Point5CodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_3_point_7_sonnet_handler import (
    Claude3Point7CodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_handler import (
    Claude4CodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_thinking_handler import (
    Claude4ThinkingCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_flash_handler import (
    Gemini2Point5FlashCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_flash_lite_handler import (
    Gemini2Point5FlashLiteCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_pro_handler import (
    Gemini2Point5ProCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_4_point_1 import (
    Gpt4Point1Prompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.kimi_k2_coder_handler import (
    KimiK2QuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.openrouter_gpt_5_handler import (
    Gpt5QuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.openrouter_gpt_5_mini_coder_handler import (
    Gpt5MiniQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.openrouter_gpt_5_nano_coder_handler import (
    Gpt5NanoQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.qwen_3_coder_handler import (
    Qwen3CoderQuerySolverPromptHandler,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt


class CodeQuerySolverPromptFactory(BaseFeaturePromptFactory):
    code_query_solver_prompts: Dict[LLModels, Type[BasePrompt]] = {
        LLModels.CLAUDE_3_POINT_7_SONNET: Claude3Point7CodeQuerySolverPromptHandler,
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5CodeQuerySolverPromptHandler,
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5ProCodeQuerySolverPromptHandler,
        LLModels.GEMINI_2_POINT_5_FLASH: Gemini2Point5FlashCodeQuerySolverPromptHandler,
        LLModels.GEMINI_2_POINT_5_FLASH_LITE: Gemini2Point5FlashLiteCodeQuerySolverPromptHandler,
        LLModels.GPT_4_POINT_1: Gpt4Point1Prompt,
        LLModels.CLAUDE_4_SONNET: Claude4CodeQuerySolverPromptHandler,
        LLModels.CLAUDE_4_SONNET_THINKING: Claude4ThinkingCodeQuerySolverPromptHandler,
        LLModels.QWEN_3_CODER: Qwen3CoderQuerySolverPromptHandler,
        LLModels.KIMI_K2: KimiK2QuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_5: Gpt5QuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_5_MINI: Gpt5MiniQuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_5_NANO: Gpt5NanoQuerySolverPromptHandler,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.code_query_solver_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
