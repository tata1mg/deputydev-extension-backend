from pydantic import BaseModel
from datetime import datetime


class PullRequestResponse(BaseModel):
    created: bool
    title: str
    description: str
    created_on: datetime
    updated_on: datetime
