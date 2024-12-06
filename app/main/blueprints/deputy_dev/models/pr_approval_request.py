from typing import Optional

from pydantic import BaseModel


class PRApprovalRequest(BaseModel):
    scm_workspace_id: str
    repo_name: str
    scm_repo_id: str
    actor: str
    scm_pr_id: str
    scm_approval_time: str
    pr_created_at: Optional[str] = None
    workspace: Optional[str] = None
    workspace_slug: Optional[str] = None
