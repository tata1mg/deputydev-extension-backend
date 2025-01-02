from typing import Optional

from pydantic import BaseModel


class AuthData(BaseModel):
    team_id: int
    advocacy_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None
