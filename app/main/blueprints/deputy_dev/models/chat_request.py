from typing import Optional, Union

from pydantic import BaseModel


class Comment(BaseModel):
    raw: str
    parent: Optional[Union[int, str]]
    path: Optional[str]
    line_number_from: Optional[int] = None  # Bitbucket old file
    line_number_to: Optional[int] = None  # Bitbucket new file
    line_number: Optional[int] = None  # Gitlab, Github line
    side: Optional[str] = None  # RIGHT: New file, LEFT: Old file Gitlab, Github
    id: Optional[int]
    parent_comment_id: Optional[int]
    context_lines: Optional[str]


class Repo(BaseModel):
    workspace: str
    pr_id: int
    repo_name: str
    commit_id: str
    workspace_id: str
    repo_id: Optional[str] = None
    workspace_slug: str = None


class Author(BaseModel):
    name: Optional[str]
    email: Optional[str]
    scm_author_id: str


class ChatRequest(BaseModel):
    comment: Comment
    repo: Repo
    author_info: Optional[Author]
