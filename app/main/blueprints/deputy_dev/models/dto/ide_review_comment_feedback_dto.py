from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class IdeReviewCommentFeedbackDTO(BaseModel):
    id: Optional[int] = None
    ide_reviews_comment_id: int
    feedback_comment: Optional[str] = None
    like: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None