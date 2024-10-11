from pydantic import BaseModel


class PRApprovalRequest(BaseModel):
    scm_workspace_id: str
    repo_name: str
    scm_repo_id: str
    actor: str
    scm_pr_id: str
    scm_approval_time: str
    pr_created_at: str
