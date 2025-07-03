from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ExtensionReviewFeedbackDTO(BaseModel):
    id: Optional[int] = None
    review_id: int
    feedback_comment: Optional[str] = None
    like: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
