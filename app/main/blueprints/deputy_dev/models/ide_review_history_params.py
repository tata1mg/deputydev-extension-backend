from pydantic import BaseModel
from typing import Optional


class ReviewHistoryParams(BaseModel):
    user_team_id: int
    repo_id: Optional[int] = None
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
