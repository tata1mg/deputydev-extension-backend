from pydantic import BaseModel


class PreviousChatPayload(BaseModel):
    query: str
    session_id: str


class PreviousChats(BaseModel):
    id: int
    summary: str
    query: str


class PreviousChatResponse(BaseModel):
    id: int
    query: str
    response: str
