from pydantic import BaseModel
from typing import Optional


class AgentCreateParams(BaseModel):
    name: str
    custom_prompt: str
    user_team_id: int


class AgentUpdateParams(BaseModel):
    id: int
    name: Optional[str] = None
    custom_prompt: Optional[str] = None
    user_team_id: Optional[int] = None