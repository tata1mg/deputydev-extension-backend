
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SessionEventsData(BaseModel):
    event_id: str
    session_id: int
    event_type: str
    lines: int
    file_path: Optional[str] = None
    client_version: str
    timestamp: datetime
    user_id: Optional[int] = None
    team_id: Optional[int] = None


class SessionEventsDTO(SessionEventsData):
    id: Optional[int] = None
    created_at: datetime
    updated_at: datetime