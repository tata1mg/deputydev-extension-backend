from app.common.constants.constants import LLModels
from app.backend_common.services.llm.base_prompt import BasePrompt


class BaseFeaturePromptFactory:
    @classmethod
    def get_prompt(cls, model_name: LLModels) -> BasePrompt:
        raise NotImplementedError("This method must be implemented in the child class")
