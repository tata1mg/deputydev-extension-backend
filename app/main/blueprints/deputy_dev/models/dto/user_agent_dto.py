from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class UserAgentDTO(BaseModel):
    id: Optional[int] = None
    agent_name: str
    display_name: Optional[str] = None
    custom_prompt: str = ""
    exclusions: List[Any] = []
    inclusions: List[Any] = []
    confidence_score: float = 0.9
    objective: str = "Responsibility of this agent is checking security issues"
    is_custom_agent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
