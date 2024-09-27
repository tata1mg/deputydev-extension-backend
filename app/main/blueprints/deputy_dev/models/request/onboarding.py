from typing import Optional

from pydantic import BaseModel


class SignUpRequest(BaseModel):
    username: str
    email: str
    org_name: str


class OnboardingRequest(BaseModel):
    team_id: int
    integration_client: str
    integration_type: str
    auth_identifier: str
    workspaces: Optional[list] = []
