from typing import Optional

from pydantic import BaseModel


class Comment(BaseModel):
    raw: str
    parent: Optional[int]
    path: Optional[str]
    line_number_from: Optional[int]
    line_number_to: Optional[int]
    id: Optional[int]


class Repo(BaseModel):
    workspace: str
    pr_id: int
    repo_name: str
    commit_id: str


class ChatRequest(BaseModel):
    comment: Comment
    repo: Repo
