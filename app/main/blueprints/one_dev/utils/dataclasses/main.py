from typing import Optional

from pydantic import BaseModel


class AuthData(BaseModel):
    user_team_id: int
    session_refresh_token: Optional[str] = None
