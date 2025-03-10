from typing import Optional

from pydantic import BaseModel


class PreviousChatPayload(BaseModel):
    query: str
    session_id: int


class PreviousChats(BaseModel):
    id: int
    summary: str
    query: Optional[str] = None


class PreviousChatResponse(BaseModel):
    id: int
    query: str
    response: str
