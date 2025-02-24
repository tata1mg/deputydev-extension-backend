from datetime import datetime

from pydantic import BaseModel


class MessageSessionData(BaseModel):
    user_team_id: int
    summary: str


class MessageSessionDTO(MessageSessionData):
    id: int
    created_at: datetime
    updated_at: datetime
