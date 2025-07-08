from typing import Dict, Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.claude_3_point_5_sonnet_handler import (
    Claude3Point5BackendAppCreatorPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.claude_4_sonnet_handler import (
    Claude4BackendAppCreatorPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.claude_4_sonnet_thinking_handler import (
    Claude4ThinkingBackendAppCreatorPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.gemini_2_point_5_flash_handler import (
    Gemini2Point5FlashBackendAppCreatorPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.gemini_2_point_5_pro_handler import (
    Gemini2Point5ProBackendAppCreatorPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.gpt_4_point_1 import (
    Gpt4Point1Prompt,
)


class BackendAppCreatorPromptFactory(BaseFeaturePromptFactory):
    backend_app_creator_prompts: Dict[LLModels, Type[BasePrompt]] = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5BackendAppCreatorPromptHandler,
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5ProBackendAppCreatorPromptHandler,
        LLModels.GEMINI_2_POINT_5_FLASH: Gemini2Point5FlashBackendAppCreatorPromptHandler,
        LLModels.GPT_4_POINT_1: Gpt4Point1Prompt,
        LLModels.CLAUDE_4_SONNET: Claude4BackendAppCreatorPromptHandler,
        LLModels.CLAUDE_4_SONNET_THINKING: Claude4ThinkingBackendAppCreatorPromptHandler,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.backend_app_creator_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
