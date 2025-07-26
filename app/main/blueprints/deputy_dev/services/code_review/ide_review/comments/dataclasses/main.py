from typing import List, Optional

from pydantic import BaseModel


class LLMCommentData(BaseModel):
    id: Optional[int] = None
    comment: str
    title: Optional[str] = None
    corrective_code: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_hash: Optional[str] = None
    tag: str
    confidence_score: Optional[float] = None
    rationale: Optional[str] = None
    bucket: Optional[str] = None


class AgentRunResult(BaseModel):
    comments: List[LLMCommentData] = None
    agent_name: str
