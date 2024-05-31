from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PullRequestResponse(BaseModel):
    id: int
    repository_name: str
    created: bool = True
    state: str
    title: str
    description: str
    issue_id: Optional[str]
    created_on: datetime
    updated_on: datetime
