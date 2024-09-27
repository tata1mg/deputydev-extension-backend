from pydantic import BaseModel


class HumanCommentRequest(BaseModel):
    scm_workspace_id: str
    repo_name: str
    scm_repo_id: str
    actor: str
    scm_pr_id: str
