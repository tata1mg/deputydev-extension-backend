from typing import Optional

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_prompt_feature_factory import (
    BasePromptFeatureFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import (
    BaseCodeReviewPrompt,
)

from .json_data_response.factory import CodeReviewJsonDataPromptFactory
from .plain_text_response.factory import CodeReviewPlainTextPromptFactory
from .xml_data_response.factory import CodeReviewXMLDataPromptFactory


class CodeReviewPromptFactory(BasePromptFeatureFactory):
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
