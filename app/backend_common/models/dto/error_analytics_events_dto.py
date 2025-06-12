from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ErrorAnalyticsEventsData(BaseModel):
    error_id: Optional[UUID] = None
    user_email: Optional[str] = None
    error_type: str
    error_data: Dict[str, Any]
    repo_name: Optional[str] = None
    error_source: Optional[str] = None
    client_version: str
    user_team_id: Optional[int] = None
    session_id: Optional[int] = None
    timestamp: datetime


class ErrorAnalyticsEventsDTO(ErrorAnalyticsEventsData):
    id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
