from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt

from .claude_3_point_5_sonnet import Claude3Point5SecurityCommentsGenerationPass1Prompt
from .claude_3_point_7_sonnet import Claude3Point7SecurityCommentsGenerationPass1Prompt
from .claude_4_sonnet import Claude4SecurityCommentsGenerationPass1Prompt


class SecurityCommentsGenerationPass1PromptFactory(BaseFeaturePromptFactory):
    prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5SecurityCommentsGenerationPass1Prompt,
        LLModels.CLAUDE_3_POINT_7_SONNET: Claude3Point7SecurityCommentsGenerationPass1Prompt,
        LLModels.CLAUDE_4_SONNET: Claude4SecurityCommentsGenerationPass1Prompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
