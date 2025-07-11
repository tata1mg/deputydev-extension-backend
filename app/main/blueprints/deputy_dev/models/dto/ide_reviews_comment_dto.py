from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .user_agent_dto import UserAgentDTO


class IdeReviewsCommentDTO(BaseModel):
    id: Optional[int] = None
    review_id: int
    comment: str
    is_deleted: bool = False
    file_path: str
    line_hash: str
    line_number: int
    tag: str
    is_valid: bool
    agents: Optional[list[UserAgentDTO]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
