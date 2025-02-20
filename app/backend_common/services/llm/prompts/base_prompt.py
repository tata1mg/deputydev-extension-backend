from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List

from app.backend_common.services.llm.dataclasses.main import (
    LLModels,
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)


class BasePrompt(ABC):
    model_name: LLModels
    prompt_type: str

    @abstractmethod
    def get_prompt(self) -> UserAndSystemMessages:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    @abstractmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    @abstractmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")
