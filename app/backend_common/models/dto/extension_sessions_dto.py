from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.backend_common.services.llm.dataclasses.main import LLModels


class ExtensionSessionData(BaseModel):
    session_id: int
    user_team_id: int
    summary: Optional[str] = None
    pinned_rank: Optional[int] = None
    status: str = "ACTIVE"
    session_type: str
    current_model: Optional[LLModels] = LLModels.CLAUDE_3_POINT_7_SONNET


class ExtensionSessionDTO(ExtensionSessionData):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
