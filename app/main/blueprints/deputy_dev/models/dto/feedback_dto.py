from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FeedbackDTO(BaseModel):
    id: Optional[int] = None
    feedback_type: str
    feedback: Optional[str]
    pr_id: Optional[int] = None
    meta_info: dict
    author_info: dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organisation_id: int
    workspace_id: int
    scm_pr_id: str
    scm: str
    repo_id: Optional[int] = None
