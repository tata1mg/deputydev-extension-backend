from pydantic import BaseModel


class AuthData(BaseModel):
    team_id: int
    user_id: int
