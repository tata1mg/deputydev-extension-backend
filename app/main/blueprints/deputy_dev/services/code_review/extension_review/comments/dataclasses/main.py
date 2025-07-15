from pydantic import BaseModel
from typing import Optional, List


class Comment(BaseModel):
    id: Optional[int]
    comment: str
    corrective_code: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    confidence_score: Optional[float] = None
    rationale: Optional[str] = None
    bucket: Optional[str] = None


class AgentRunResult(BaseModel):
    comments: List[Comment] = None
    agent_name: str
