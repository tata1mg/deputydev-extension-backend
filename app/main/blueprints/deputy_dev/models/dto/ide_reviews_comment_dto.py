from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from .ide_review_comment_feedback_dto import IdeReviewCommentFeedbackDTO
from app.main.blueprints.deputy_dev.constants.constants import IdeReviewCommentStatus

from .user_agent_dto import UserAgentDTO


class IdeReviewsCommentDTO(BaseModel):
    id: Optional[int] = None
    title: str
    review_id: int
    comment: str
    confidence_score: float = 0
    rationale: Optional[str] = ""
    corrective_code: Optional[str] = ""
    is_deleted: bool = False
    file_path: str
    line_hash: str
    line_number: int
    tag: str
    is_valid: bool
    agents: Optional[list[UserAgentDTO]] = []
    feedback: Optional[IdeReviewCommentFeedbackDTO] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
    comment_status: Optional[str] = IdeReviewCommentStatus.NOT_REVIEWED.value
