from pydantic import BaseModel


class IssueCommentRequest(BaseModel):
    """Data class for issue comment request"""

    issue_id: str
    issue_description: str
    issue_title: str
    issue_comment: str
    repo_name: str
    workspace: str
    workspace_slug: str
    scm_workspace_id: str
    vcs_type: str
