from typing import Any, Dict, List, Type

from pydantic import BaseModel

from app.backend_common.models.dto.message_thread_dto import LLModels, MessageData
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseGpt4Point1NanoPrompt(BasePrompt):
    model_name = LLModels.GPT_4_POINT_1_NANO

    @classmethod
    def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    def get_text_format(cls) -> Type[BaseModel]:
        raise NotImplementedError("This method must be implemented in the child class")
