from pydantic import BaseModel


class PRCloseRequest(BaseModel):
    pr_state: str
    pr_id: str
    repo_name: str
    repo_id: str
    workspace: str
    workspace_slug: str
    workspace_id: str
    pr_created_at: str
    pr_closed_at: str
