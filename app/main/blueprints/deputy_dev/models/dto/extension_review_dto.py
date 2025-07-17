from datetime import datetime
from typing import Optional, Dict, Any, List
from .ide_reviews_comment_dto import IdeReviewsCommentDTO
from pydantic import BaseModel, ConfigDict


class ExtensionReviewDTO(BaseModel):
    id: Optional[int] = None
    title: str
    review_status: str
    repo_id: int
    user_team_id: int
    loc: int
    reviewed_files: List[str]
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
    source_commit: Optional[str] = None
    target_commit: Optional[str] = None
    execution_time_seconds: Optional[int] = None
    fail_message: Optional[str] = None
    review_datetime: Optional[datetime] = None
    comments: Optional[List[IdeReviewsCommentDTO]] = []
    is_deleted: bool = False
    deletion_datetime: Optional[datetime] = None
    meta_info: Optional[dict] = None
    diff_s3_url: Optional[str] = None
    session_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
