from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)

from .gemini_2_point_5_flash import Gemini2Point5FlashRelevantChatFilterPrompt


class ChatRankingPromptFactory(BaseFeaturePromptFactory):
    chat_re_ranking_prompts = {LLModels.GEMINI_2_POINT_5_FLASH: Gemini2Point5FlashRelevantChatFilterPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.chat_re_ranking_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
