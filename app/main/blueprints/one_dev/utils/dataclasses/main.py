from enum import Enum

from pydantic import BaseModel


class AuthData(BaseModel):
    user_team_id: int


class DeputyDevClientType(Enum):
    CLI_CLIENT = "CLI"
    VSCODE_EXT_CLIENT = "VSCODE"
