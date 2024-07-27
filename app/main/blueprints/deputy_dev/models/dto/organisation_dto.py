from datetime import datetime

from pydantic import BaseModel


class OrganisationDTO(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    status: str
    email: str
