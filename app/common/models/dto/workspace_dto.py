from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WorkspaceDTO(BaseModel):
    id: int
    scm_workspace_id: str
    name: str
    scm: str  # Assuming scm_type is a string; adjust if it's an enum or another type
    created_at: datetime
    updated_at: datetime
    integration_id: Optional[int]
    slug: Optional[str]
    team_id: int

    model_config = ConfigDict(from_attributes=True)
