from pydantic import BaseModel


class SignUpRequest(BaseModel):
    username: str
    email: str
    org_name: str
