from datetime import datetime

from pydantic import BaseModel


class PullRequestResponse(BaseModel):
    title: str
    description: str
    issue_id: str
    created_on: datetime
    updated_on: datetime