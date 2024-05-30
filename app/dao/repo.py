from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class PullRequestResponse(BaseModel):
    title: str
    description: str
    issue_id: Optional[str]
    created_on: datetime
    updated_on: datetime
