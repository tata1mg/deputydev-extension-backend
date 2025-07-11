from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserAgentCommentMappingDTO(BaseModel):
    id: Optional[int] = None
    agent_id: int
    comment_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
