from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)

from .claude_3_point_5_sonnet import Claude3Point5RelevantChatFilterPrompt


class ChatRankingPromptFactory(BaseFeaturePromptFactory):
    chat_re_ranking_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5RelevantChatFilterPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.chat_re_ranking_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
