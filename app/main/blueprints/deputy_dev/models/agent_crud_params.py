from pydantic import BaseModel
from typing import Optional


class AgentParams(BaseModel):
    id: Optional[int] = None
    name: str
    custom_prompt: str
    user_team_id: int
