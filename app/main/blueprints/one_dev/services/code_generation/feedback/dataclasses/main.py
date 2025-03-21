from pydantic import BaseModel

from app.backend_common.constants.feedbacks import UpvoteDownvoteFeedbacks


class CodeGenerationFeedbackInput(BaseModel):
    feedback: UpvoteDownvoteFeedbacks
    job_id: int
