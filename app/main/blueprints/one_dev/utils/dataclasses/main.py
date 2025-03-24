from typing import Optional, Tuple
from pydantic import BaseModel


class AuthData(BaseModel):
    user_team_id: int
    refresh_session_data: Optional[Tuple[str, str, str]] = None
