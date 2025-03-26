from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients
from app.backend_common.constants.constants import PixelEvents


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


class PixelEventsDTO(PixelEventsData):
    id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
