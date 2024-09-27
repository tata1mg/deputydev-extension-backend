from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PullRequestResponse(BaseModel):
    id: int
    state: str
    title: str
    description: Optional[str]
    issue_id: Optional[str] = None
    branch_name: str
    created_on: datetime
    updated_on: datetime
    commit_id: Optional[str] = None
    diff_refs: Optional[dict] = None
