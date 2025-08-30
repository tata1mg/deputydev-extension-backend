from enum import Enum
from typing import Optional

from deputydev_core.utils.constants.auth import AuthStatus
from deputydev_core.utils.constants.enums import Clients
from pydantic import BaseModel


class AuthData(BaseModel):
    user_team_id: int
    session_refresh_token: Optional[str] = None


class AuthProvider(Enum):
    SUPABASE = "SUPABASE"
    FAKEAUTH = "FAKEAUTH"


class ClientData(BaseModel):
    client: Clients
    client_version: str


class AuthSessionData(BaseModel):
    status: AuthStatus
    encrypted_session_data: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    error_message: Optional[str] = None


class AuthTokenData(BaseModel):
    valid: bool
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
