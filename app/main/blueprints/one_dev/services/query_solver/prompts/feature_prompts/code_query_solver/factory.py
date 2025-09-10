from typing import Dict, Type

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_3_point_7_sonnet_handler import (
    Claude3Point7CustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_handler import (
    Claude4CustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_thinking_handler import (
    Claude4ThinkingCustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_flash_handler import (
    Gemini2Point5FlashCustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_flash_lite_handler import (
    Gemini2Point5FlashLiteCustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_pro_handler import (
    Gemini2Point5ProCustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_4_point_1_handler import (
    Gpt4Point1CustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_5_handler import (
    Gpt5CustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_5_mini_handler import (
    Gpt5MiniCustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_5_nano_handler import (
    Gpt5NanoCustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.grok_code_fast_1_handler import (
    GrokCodeFast1CustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.kimi_k2_coder_handler import (
    KimiK2CustomCodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.qwen_3_coder_handler import (
    Qwen3CoderCustomCodeQuerySolverPromptHandler,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt


class CodeQuerySolverPromptFactory(BaseFeaturePromptFactory):
    custom_code_query_solver_prompts: Dict[LLModels, Type[BasePrompt]] = {
        LLModels.CLAUDE_3_POINT_7_SONNET: Claude3Point7CustomCodeQuerySolverPromptHandler,
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5ProCustomCodeQuerySolverPromptHandler,
        LLModels.GEMINI_2_POINT_5_FLASH: Gemini2Point5FlashCustomCodeQuerySolverPromptHandler,
        LLModels.GEMINI_2_POINT_5_FLASH_LITE: Gemini2Point5FlashLiteCustomCodeQuerySolverPromptHandler,
        LLModels.CLAUDE_4_SONNET: Claude4CustomCodeQuerySolverPromptHandler,
        LLModels.CLAUDE_4_SONNET_THINKING: Claude4ThinkingCustomCodeQuerySolverPromptHandler,
        LLModels.QWEN_3_CODER: Qwen3CoderCustomCodeQuerySolverPromptHandler,
        LLModels.KIMI_K2: KimiK2CustomCodeQuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_5: Gpt5CustomCodeQuerySolverPromptHandler,
        LLModels.OPENROUTER_GROK_CODE_FAST_1: GrokCodeFast1CustomCodeQuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_5_MINI: Gpt5MiniCustomCodeQuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_5_NANO: Gpt5NanoCustomCodeQuerySolverPromptHandler,
        LLModels.OPENROUTER_GPT_4_POINT_1: Gpt4Point1CustomCodeQuerySolverPromptHandler,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.custom_code_query_solver_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
