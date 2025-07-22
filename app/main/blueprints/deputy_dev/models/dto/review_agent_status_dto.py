from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ReviewAgentStatusDTO(BaseModel):
    id: Optional[int] = None
    review_id: int
    agent_id: int
    meta_info: Optional[Dict[str, Any]] = None
    llm_model: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
