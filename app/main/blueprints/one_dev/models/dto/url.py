from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UrlDto(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    user_team_id: int
    is_deleted: bool = False
    last_indexed: Optional[datetime] = None
