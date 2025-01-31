from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamDTO(BaseModel):
    id: Optional[int] = None
    name: str
    llm_model: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
