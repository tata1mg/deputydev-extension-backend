from pydantic import BaseModel


class AuthData(BaseModel):
    user_team_id: int
