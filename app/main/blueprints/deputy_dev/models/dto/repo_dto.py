from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RepoDTO(BaseModel):
    id: Optional[int] = None
    name: str
    organisation_id: int
    scm: str
    workspace_id: int
    scm_repo_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
