from typing import Type

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseFeaturePromptFactory:
    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    def get_text_format(cls, model_name: LLModels) -> Type[BaseModel]:
        raise NotImplementedError("This method must be implemented in the child class")
