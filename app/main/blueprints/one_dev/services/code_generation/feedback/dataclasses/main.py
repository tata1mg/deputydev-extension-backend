from pydantic import BaseModel

from app.common.constants.feedbacks import UpvoteDownvoteFeedbacks


class CodeGenerationFeedbackInput(BaseModel):
    feedback: UpvoteDownvoteFeedbacks
    job_id: int
