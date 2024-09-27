from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamDTO(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    llm_model: Optional[str]
