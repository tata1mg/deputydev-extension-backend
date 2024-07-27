from datetime import datetime

from pydantic import BaseModel

from app.main.blueprints.deputy_dev.models.dto.organisation_dto import OrganisationDTO


class WorkspaceDTO(BaseModel):
    id: int
    scm_workspace_id: str
    name: str
    organisation_info: OrganisationDTO
    scm: str  # Assuming scm_type is a string; adjust if it's an enum or another type
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
