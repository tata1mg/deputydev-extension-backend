from pydantic import BaseModel
from typing import Optional, List


class Comment(BaseModel):
    comment: str
    corrective_code: Optional[str] = None
    file_path: str
    line_number: int
    confidence_score: float
    rationale: str
    bucket: str


class AgentRunResult(BaseModel):
    comments: List[Comment] = None
    agent_name: str
