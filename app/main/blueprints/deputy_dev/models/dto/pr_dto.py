from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from app.backend_common.constants.constants import PRStatus


class PullRequestDTO(BaseModel):
    id: Optional[int] = None
    review_status: str
    quality_score: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    team_id: int
    scm: str
    workspace_id: int
    repo_id: int
    scm_pr_id: str
    scm_author_id: str
    author_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    meta_info: Optional[Dict[str, Any]] = None
    source_branch: str
    destination_branch: str
    scm_creation_time: Optional[datetime] = None
    scm_close_time: Optional[datetime] = None
    commit_id: str
    destination_commit_id: str
    iteration: Optional[int] = None
    loc_changed: Optional[int] = 0
    pr_state: str = PRStatus.OPEN.value
    scm_approval_time: Optional[datetime] = None
    session_id: Optional[int] = None
    session_ids: Optional[list[int]] = None

    model_config = ConfigDict(from_attributes=True)
