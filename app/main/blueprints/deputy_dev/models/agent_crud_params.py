from typing import Optional

from pydantic import BaseModel


class AgentCreateParams(BaseModel):
    name: str
    custom_prompt: str
    user_team_id: int
    agent_name: str = "custom_commenter_agent"


class AgentUpdateParams(BaseModel):
    id: int
    name: Optional[str] = None
    custom_prompt: Optional[str] = None
    user_team_id: Optional[int] = None
