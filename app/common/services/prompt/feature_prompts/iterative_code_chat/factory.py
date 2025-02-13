from app.backend_common.services.llm.base_prompt import BasePrompt
from app.common.constants.constants import LLModels
from app.common.services.prompt.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.common.services.prompt.feature_prompts.iterative_code_chat.claude_3_point_5_sonnet import (
    Claude3Point5IterativeCodeChatPrompt,
)


class IterativeCodeChatPromptFactory(BaseFeaturePromptFactory):
    iterative_code_chat_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5IterativeCodeChatPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> BasePrompt:
        prompt_class = cls.iterative_code_chat_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
