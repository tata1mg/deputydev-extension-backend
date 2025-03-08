from datetime import datetime
from typing import Optional

from deputydev_core.utils.constants.feedbacks import UpvoteDownvoteFeedbacks
from pydantic import BaseModel


class JobFeedbackDTO(BaseModel):
    id: Optional[int] = None
    feedback: UpvoteDownvoteFeedbacks
    job_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
