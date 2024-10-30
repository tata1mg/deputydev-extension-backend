from typing import Optional

from pydantic import BaseModel


class PRCommentsDTO(BaseModel):
    id: Optional[int] = None
    iteration: int
    llm_confidence_score: float
    llm_source_model: str
    team_id: int
    scm: str
    workspace_id: int
    repo_id: int
    pr_id: int
    scm_comment_id: str
    scm_author_id: str
    author_name: str
    meta_info: Optional[dict] = None

    class Config:
        orm_mode = True
