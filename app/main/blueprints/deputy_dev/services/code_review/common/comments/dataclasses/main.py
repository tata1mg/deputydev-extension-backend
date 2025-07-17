from typing import List, Optional

from pydantic import BaseModel


class CommentBuckets(BaseModel):
    name: str
    agent_id: str


class ParsedCommentData(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    file_path: str
    line_number: str
    line_hash: Optional[str] = None
    tag: Optional[str] = None
    comment: str
    buckets: List[CommentBuckets] = []
    confidence_score: float
    corrective_code: Optional[str] = None
    model: Optional[str] = None
    is_valid: Optional[bool] = None
    is_summarized: bool = False
    rationale: str


class ParsedAggregatedCommentData(BaseModel):
    titles: Optional[List[str]] = []
    file_path: str
    line_number: str
    line_hash: Optional[str] = None
    comments: List[str] = []
    tags: List[str] = []
    comment_ids: Optional[List[int]] = []
    buckets: List[CommentBuckets] = []
    agent_ids: List[str] = []
    corrective_code: List[str] = []
    confidence_scores: List[float] = []
    confidence_score: float
    model: Optional[str] = None
    is_valid: Optional[bool] = None
    rationales: List[str]
