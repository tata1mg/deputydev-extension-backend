from typing import Optional

from pydantic import BaseModel


class PRCloseRequest(BaseModel):
    pr_state: str
    scm_pr_id: str
    repo_name: str
    scm_repo_id: str
    workspace: str
    workspace_slug: str
    scm_workspace_id: str
    pr_created_at: str
    pr_closed_at: str
    destination_branch: Optional[str] = None
