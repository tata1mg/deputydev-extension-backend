from typing import Optional

from pydantic import BaseModel, Field


class SmartCodeReqeustModel(BaseModel):
    branch: str
    repo_name: str
    pr_id: int
    confidence_score: Optional[int]
    pr_type: str = Field(enum=["created", "updated"])
