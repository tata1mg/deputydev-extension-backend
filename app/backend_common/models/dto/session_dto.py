from datetime import datetime

from pydantic import BaseModel


class SessionDTO(BaseModel):
    id: int
    summary: str
    user_team_id: int
    created_at: datetime
    updated_at: datetime
