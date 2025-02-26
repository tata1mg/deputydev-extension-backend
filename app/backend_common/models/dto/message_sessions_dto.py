from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageSessionData(BaseModel):
    user_team_id: int
    summary: Optional[str] = None
    client: str
    client_version: Optional[str] = None


class MessageSessionDTO(MessageSessionData):
    id: int
    created_at: datetime
    updated_at: datetime
