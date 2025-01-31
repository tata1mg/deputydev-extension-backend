from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserTeamDTO(BaseModel):
    id: Optional[int] = None
    user_id: int
    team_id: int
    role: str
    last_pr_authored_or_reviewed_at: Optional[datetime] = None
    is_owner: bool
    is_billable: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
