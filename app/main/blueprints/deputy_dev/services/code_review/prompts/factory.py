from typing import Optional

from json_data_response.factory import CodeReviewJsonDataPromptFactory
from plain_text_response.factory import CodeReviewPlainTextPromptFactory
from xml_data_response.factory import CodeReviewXMLDataPromptFactory

from app.backend_common.services.llm.dataclasses.main import LLModels
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import (
    BaseCodeReviewPrompt,
)


class CodeReviewPromptFactory:
    RESPONSE_TYPE_BASED_PROMPTS = {
        "xml": CodeReviewXMLDataPromptFactory,
        "json": CodeReviewJsonDataPromptFactory,
        "plain_text": CodeReviewPlainTextPromptFactory,
    }

    @classmethod
    def get_prompt_obj(
        cls,
        model: LLModels,
        prompt_return_type: str,
        should_parse: bool,
        user_message: str,
        system_message: Optional[str] = None,
    ) -> BaseCodeReviewPrompt:

        response_type_to_use = prompt_return_type
        if not should_parse:
            response_type_to_use = "plain_text"

        prompt_class = cls.RESPONSE_TYPE_BASED_PROMPTS[response_type_to_use].get_prompt_class(model=model)
        return prompt_class(user_message=user_message, system_message=system_message)
