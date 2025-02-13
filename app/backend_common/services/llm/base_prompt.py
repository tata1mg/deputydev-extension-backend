from abc import ABC, abstractmethod
from typing import Any, Dict

from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
from app.common.constants.constants import LLModels


class BasePrompt(ABC):
    model_name: LLModels
    prompt_type: str

    @abstractmethod
    def get_prompt(self) -> UserAndSystemMessages:
        raise NotImplementedError("This method must be implemented in the child class")

    @abstractmethod
    def get_parsed_result(self, llm_response: str) -> Dict[str, Any]:
        raise NotImplementedError("This method must be implemented in the child class")
