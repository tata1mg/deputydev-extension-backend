from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserExtensionRepoDTO(BaseModel):
    id: Optional[int] = None
    repo_name: str
    repo_id: str
    user_team_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None