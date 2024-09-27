from pydantic import BaseModel


class CodeReviewRequest(BaseModel):
    pr_id: int
    repo_name: str
    request_id: str
    workspace: str
    prompt_version: str
    vcs_type: str
    workspace_id: str
    workspace_slug: str
