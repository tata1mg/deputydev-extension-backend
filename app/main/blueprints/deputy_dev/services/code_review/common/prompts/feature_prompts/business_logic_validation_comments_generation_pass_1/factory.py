from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from .claude_3_point_5_sonnet import (
    Claude3Point5BusinessLogicValidationCommentsGenerationPass1Prompt,
)
from .claude_3_point_7_sonnet import (
    Claude3Point7BusinessLogicValidationCommentsGenerationPass1Prompt,
)
from .claude_4_sonnet import Claude4BusinessLogicValidationCommentsGenerationPass1Prompt
from .claude_4_point_5_sonnet import Claude4Point5BusinessLogicValidationCommentsGenerationPass1Prompt


class BusinessLogicValidationCommentsGenerationPass1PromptFactory(BaseFeaturePromptFactory):
    prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5BusinessLogicValidationCommentsGenerationPass1Prompt,
        LLModels.CLAUDE_3_POINT_7_SONNET: Claude3Point7BusinessLogicValidationCommentsGenerationPass1Prompt,
        LLModels.CLAUDE_4_SONNET: Claude4BusinessLogicValidationCommentsGenerationPass1Prompt,
        LLModels.CLAUDE_4_POINT_5_SONNET: Claude4Point5BusinessLogicValidationCommentsGenerationPass1Prompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
