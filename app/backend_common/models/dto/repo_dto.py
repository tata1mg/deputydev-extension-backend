from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RepoDTO(BaseModel):
    id: Optional[int] = None
    name: str
    team_id: int
    scm: Optional[str] = None
    workspace_id: Optional[int] = None
    scm_repo_id: Optional[str] = None
    repo_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
