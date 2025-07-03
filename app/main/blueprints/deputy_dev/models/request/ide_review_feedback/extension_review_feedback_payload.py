from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ExtensionReviewFeedbackPayload(BaseModel):
    feedback_comment: Optional[str] = None
    like: Optional[bool] = None
