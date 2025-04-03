from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExtensionSessionData(BaseModel):
    session_id: int
    user_team_id: int
    summary: Optional[str] = None
    pinned_rank: Optional[int] = None
    status: str = "ACTIVE"
    session_type: str


class ExtensionSessionDTO(ExtensionSessionData):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
