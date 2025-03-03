from pydantic import BaseModel

from deputydev_core.utils.constants.feedbacks import UpvoteDownvoteFeedbacks


class CodeGenerationFeedbackInput(BaseModel):
    feedback: UpvoteDownvoteFeedbacks
    job_id: int
