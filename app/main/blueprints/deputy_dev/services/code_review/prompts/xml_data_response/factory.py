from typing import Type
from app.backend_common.services.llm.dataclasses.main import LLModels
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import BaseCodeReviewPrompt
from .claude_3_point_5_sonnet import Claude3Point5XMLDataResponsePrompt


class CodeReviewXMLDataPromptFactory:
    prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5XMLDataResponsePrompt
    }

    @classmethod
    def get_prompt_class(cls, model: LLModels) -> Type[BaseCodeReviewPrompt]:
        prompt_class = cls.prompts.get(model)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model}")
        return prompt_class
