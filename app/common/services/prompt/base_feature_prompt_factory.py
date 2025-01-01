from app.common.constants.constants import LLModels
from app.common.services.prompt.base_prompt import BasePrompt


class BaseFeaturePromptFactory:
    @classmethod
    def get_prompt(cls, model_name: LLModels) -> BasePrompt:
        raise NotImplementedError("This method must be implemented in the child class")
