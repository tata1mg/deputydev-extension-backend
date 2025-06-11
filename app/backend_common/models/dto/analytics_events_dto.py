from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients


class AnalyticsEventsData(BaseModel):
    event_id: Optional[UUID] = None
    session_id: int
    event_type: str
    client_version: str
    client: Clients
    timestamp: datetime
    user_team_id: int
    event_data: Dict[str, Any]


class AnalyticsEventsDTO(AnalyticsEventsData):
    id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
