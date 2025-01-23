from typing import Optional

from pydantic import BaseModel


class PRConfig(BaseModel):
    workspace_id: int
    repo_name: str
    source_branch: str
    destination_branch: str
    pr_title_prefix: Optional[str] = None
    commit_message_prefix: Optional[str] = None
    parent_source_branch: str
