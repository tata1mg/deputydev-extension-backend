from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.main.blueprints.deputy_dev.constants.constants import PRStatus


class ExperimentsDTO(BaseModel):
    id: Optional[int] = None
    scm_pr_id: str
    team_id: int
    workspace_id: int
    repo_id: int
    cohort: str
    scm: str
    pr_id: int
    review_status: str
    close_time_in_sec: Optional[int] = None
    human_comment_count: Optional[int] = None
    llm_comment_count: Optional[int] = None
    scm_creation_time: Optional[datetime] = None
    scm_close_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pr_state: str = PRStatus.OPEN.value

    class Config:
        orm_mode = True
