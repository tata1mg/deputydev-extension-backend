from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class UserAgentDTO(BaseModel):
    id: Optional[int] = None
    agent_name: Optional[str] = None
    user_team_id: Optional[int] = None
    display_name: Optional[str] = None
    custom_prompt: Optional[str] = ""
    exclusions: Optional[List[Any]] = []
    inclusions: Optional[List[Any]] = []
    confidence_score: Optional[float] = 0.9
    objective: Optional[str] = None
    is_custom_agent: bool = False
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
