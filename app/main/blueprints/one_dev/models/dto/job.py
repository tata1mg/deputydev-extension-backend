from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class JobDTO(BaseModel):
    id: Optional[int] = None
    type: str
    status: str
    session_id: str
    final_output: Optional[Dict[str, Any]] = None
    meta_info: Optional[Dict[str, Any]] = None
    user_team_id: int
    loc: Optional[int] = None
    llm_model: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
