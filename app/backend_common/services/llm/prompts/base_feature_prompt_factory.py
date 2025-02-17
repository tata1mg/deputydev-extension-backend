from typing import Type
from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseFeaturePromptFactory:
    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        raise NotImplementedError("This method must be implemented in the child class")
