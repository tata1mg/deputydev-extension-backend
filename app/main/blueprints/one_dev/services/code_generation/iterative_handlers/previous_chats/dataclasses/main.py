from enum import Enum

from pydantic import BaseModel


class RerankerDecision(Enum):
    SAFE_TO_HANDLE = "SAFE_TO_HANDLE"
    UNSAFE_TO_HANDLE = "UNSAFE_TO_HANDLE"
    NEED_TO_CHECK_TOKENS = "NEED_TO_CHECK_TOKENS"


class PreviousChatPayload(BaseModel):
    query: str
    session_id: int


class PreviousChats(BaseModel):
    id: int
    summary: str
    query: str


class PreviousChatResponse(BaseModel):
    id: int
    query: str
    response: str
