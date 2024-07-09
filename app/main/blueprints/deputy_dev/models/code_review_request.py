from pydantic import BaseModel


class CodeReviewRequest(BaseModel):
    pr_id: int
    repo_name: str
    request_id: str
    prompt_version: str
