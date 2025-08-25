from enum import Enum
from typing import Optional

from openai import BaseModel


class SessionsListTypes(Enum):
    PINNED = "PINNED"
    UNPINNED = "UNPINNED"


class FormattedSession(BaseModel):
    id: int
    summary: str
    age: str
    pinned_rank: Optional[int] = None
    created_at: str
    updated_at: str


class PastSessionsInput(BaseModel):
    user_team_id: int
    session_type: str
    sessions_list_type: SessionsListTypes
    limit: Optional[int] = None
    offset: Optional[int] = None


class PinnedRankUpdateInput(BaseModel):
    session_id: int
    user_team_id: int
    sessions_list_type: SessionsListTypes
    pinned_rank: Optional[int] = None
