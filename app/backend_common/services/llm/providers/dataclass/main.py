from typing import Any, Dict

from pydantic import BaseModel

from app.backend_common.constants.constants import LLModels


class LLMUsage(BaseModel):
    input: int
    output: int


class LLMMeta(BaseModel):
    llm_model: LLModels
    prompt_type: str
    token_usage: LLMUsage


class LLMCallResponse(BaseModel):
    raw_llm_response: str
    parsed_llm_data: Dict[str, Any]
    raw_prompt: str
    llm_meta: LLMMeta
