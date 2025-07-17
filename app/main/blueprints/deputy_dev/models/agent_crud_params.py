from pydantic import BaseModel
from typing import Optional


class AgentParams(BaseModel):
    id: Optional[int] = None
    name: str
    custom_prompt: str
    user_team_id: int
    confidence_score: Optional[float] = 0.9
    is_custom_agent: Optional[bool] = True
    exclusions: Optional[list] = []
    inclusions: Optional[list] = []
    objective: Optional[str] = ""
