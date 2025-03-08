from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import (
    BaseCodeReviewPrompt,
)

from .claude_3_point_5_sonnet import Claude3Point5JsonDataResponsePrompt
from .gpt_4o import GPT4OJsonDataResponsePrompt


class CodeReviewJsonDataPromptFactory:
    prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5JsonDataResponsePrompt,
        LLModels.GPT_4O: GPT4OJsonDataResponsePrompt,
    }

    @classmethod
    def get_prompt_class(cls, model: LLModels) -> Type[BaseCodeReviewPrompt]:
        prompt_class = cls.prompts.get(model)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model}")
        return prompt_class
