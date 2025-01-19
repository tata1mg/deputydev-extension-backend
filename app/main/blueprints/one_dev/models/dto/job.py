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
    team_id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
