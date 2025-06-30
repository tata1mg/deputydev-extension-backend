from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IdeReviewsCommentDTO(BaseModel):
    id: Optional[int] = None
    review_id: int
    comment: str
    agent_id: int
    is_deleted: bool = False
    file_path: str
    file_hash: str
    line_number: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None