from pydantic import BaseModel, Field

from app.utils import get_request_time


class CodeReviewRequest(BaseModel):
    pr_id: int
    repo_name: str
    request_time: str = Field(default_factory=get_request_time)
