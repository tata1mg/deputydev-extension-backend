from abc import ABC, abstractmethod
from typing import AsyncIterator, List

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
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
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[BaseModel]:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    @abstractmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError("This method must be implemented in the child class")
