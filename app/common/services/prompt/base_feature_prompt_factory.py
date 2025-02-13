from app.backend_common.services.llm.base_prompt import BasePrompt
from app.common.constants.constants import LLModels


class BaseFeaturePromptFactory:
    @classmethod
    def get_prompt(cls, model_name: LLModels) -> BasePrompt:
        raise NotImplementedError("This method must be implemented in the child class")
