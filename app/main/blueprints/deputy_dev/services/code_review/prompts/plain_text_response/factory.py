from typing import Type

from app.backend_common.services.llm.dataclasses.main import LLModels
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import (
    BaseCodeReviewPrompt,
)

from .gpt_4o import GPT4OPlainTextResponsePrompt


class CodeReviewPlainTextPromptFactory:
    prompts = {LLModels.GPT_4O: GPT4OPlainTextResponsePrompt}

    @classmethod
    def get_prompt_class(cls, model: LLModels) -> Type[BaseCodeReviewPrompt]:
        prompt_class = cls.prompts.get(model)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model}")
        return prompt_class
