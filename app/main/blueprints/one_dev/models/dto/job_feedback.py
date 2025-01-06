from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.common.constants.feedbacks import UpvoteDownvoteFeedbacks


class JobFeedbackDTO(BaseModel):
    id: Optional[int] = None
    feedback: UpvoteDownvoteFeedbacks
    job_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
