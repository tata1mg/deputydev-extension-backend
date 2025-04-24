from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UrlDto(BaseModel):
    id: Optional[int] = None
    name: str
    url: str
    user_team_id: int
    is_deleted: bool = False
    last_indexed: Optional[datetime] = None
