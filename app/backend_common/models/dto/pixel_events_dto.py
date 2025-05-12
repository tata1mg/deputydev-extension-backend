from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.backend_common.constants.constants import PixelEvents
from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients


class PixelEventsData(BaseModel):
    event_id: str
    session_id: int
    event_type: PixelEvents
    lines: int
    file_path: Optional[str] = None
    client_version: str
    client: Clients
    timestamp: datetime
    user_id: int
    team_id: int
    source: Optional[str] = None


class PixelEventsDTO(PixelEventsData):
    id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
