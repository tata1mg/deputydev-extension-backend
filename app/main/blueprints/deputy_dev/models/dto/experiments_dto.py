from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExperimentsDTO(BaseModel):
    id: Optional[int] = None
    scm_pr_id: str
    organisation_id: int
    workspace_id: int
    repo_id: int
    cohort: str
    scm: str
    pr_id: int
    review_status: str
    merge_time_in_sec: Optional[int] = None
    human_comment_count: Optional[int] = None
    llm_comment_count: Optional[int] = None
    scm_creation_time: Optional[datetime] = None
    scm_merge_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
