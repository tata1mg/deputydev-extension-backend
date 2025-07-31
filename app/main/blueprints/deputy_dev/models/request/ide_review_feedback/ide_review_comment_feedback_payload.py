from typing import Optional

from pydantic import BaseModel


class IdeReviewCommentFeedbackPayload(BaseModel):
    feedback_comment: Optional[str] = None
    like: Optional[bool] = None
