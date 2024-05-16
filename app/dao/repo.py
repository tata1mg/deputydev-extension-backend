from datetime import datetime

from pydantic import BaseModel


class PullRequestResponse(BaseModel):
    created: bool
    title: str
    description: str
    created_on: datetime
    updated_on: datetime
