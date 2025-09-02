from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from app.backend_common.utils.dataclasses.main import Clients


class AnalyticsEventsData(BaseModel):
    event_id: Optional[UUID] = None
    session_id: Optional[int] = None
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
