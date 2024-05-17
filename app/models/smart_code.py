from typing import Optional

from pydantic import BaseModel, Field

from app.constants.constants import CONFIDENCE_SCORE
from app.constants.repo import VCSTypes


class SmartCodeReqeustModel(BaseModel):
    branch: str
    repo_name: str
    pr_id: int
    pr_type: str = Field(enum=["created", "updated"])
    vcs_type: VCSTypes = VCSTypes.bitbucket.value
    confidence_score: Optional[float] = CONFIDENCE_SCORE
