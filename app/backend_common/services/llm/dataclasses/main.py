from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.common.constants.constants import LLModels


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


class UserAndSystemMessages(BaseModel):
    user_message: str
    system_message: Optional[str] = None


class ConversationRole(Enum):
    USER = "user"
    SYSTEM = "assistant"


class ConversationTurn(BaseModel):
    role: ConversationRole
    content: str


class ConversationTools(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class PromptCacheConfig(BaseModel):
    conversation: bool
    tools: bool
    system_message: bool
