from typing import List, Optional

from pydantic import BaseModel


class CommentBuckets(BaseModel):
    name: str
    agent_id: str


class ParsedCommentData(BaseModel):
    file_path: str
    line_number: str
    comment: str
    buckets: List[CommentBuckets] = []
    confidence_score: float
    corrective_code: Optional[str] = None
    model: str
    is_valid: Optional[bool] = None
    is_summarized: bool = False
    rationale: str


class ParsedAggregatedCommentData(BaseModel):
    file_path: str
    line_number: str
    comments: List[str] = []
    buckets: List[CommentBuckets] = []
    agent_ids: List[str] = []
    corrective_code: List[str] = []
    confidence_scores: List[float] = []
    confidence_score: float
    model: str
    is_valid: Optional[bool] = None
    rationales: List[str]
