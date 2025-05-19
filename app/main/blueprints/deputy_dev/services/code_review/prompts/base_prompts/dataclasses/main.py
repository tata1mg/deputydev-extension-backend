from typing import Optional

from pydantic import BaseModel


class LLMCommentData(BaseModel):
    comment: str
    corrective_code: Optional[str] = None
    file_path: str
    line_number: str
    confidence_score: float
    bucket: str
    rationale: str
