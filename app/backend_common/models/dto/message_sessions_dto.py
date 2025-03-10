from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients


class MessageSessionData(BaseModel):
    user_team_id: int
    summary: Optional[str] = None
    client: Clients
    client_version: Optional[str] = None
    status: str = "ACTIVE"


class MessageSessionDTO(MessageSessionData):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
