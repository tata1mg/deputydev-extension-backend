from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PullRequestResponse(BaseModel):
    id: int
    state: str
    title: str
    description: str
    issue_id: Optional[str]
    branch_name: str
    created_on: datetime
    updated_on: datetime
