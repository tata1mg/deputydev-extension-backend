from typing import Optional
from pydantic import BaseModel


class IdeReviewCommentFeedbackDTO(BaseModel):
    feedback_comment: Optional[str] = None
    like: Optional[bool] = None
