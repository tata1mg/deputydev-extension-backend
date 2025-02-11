from abc import ABC, abstractmethod
from typing import Any, Dict

from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
from app.common.constants.constants import LLModels


class BasePrompt(ABC):
    model_name: LLModels
    prompt_type: str

    @classmethod
    @abstractmethod
    def get_prompt(cls) -> UserAndSystemMessages:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    @abstractmethod
    def get_parsed_result(cls, llm_response: str) -> Dict[str, Any]:
        raise NotImplementedError("This method must be implemented in the child class")
