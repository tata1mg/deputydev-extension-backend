from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict

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

    @abstractmethod
    def get_parsed_result(self, llm_response: NonStreamingResponse) -> Dict[str, Any]:
        raise NotImplementedError("This method must be implemented in the child class")

    async def get_parsed_streaming_events(self, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        return llm_response.content
