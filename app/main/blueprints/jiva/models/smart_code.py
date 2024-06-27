from typing import Optional

from pydantic import BaseModel, Field

from app.main.blueprints.deputy_dev.constants.repo import VCSTypes


class SmartCodeReqeustModel(BaseModel):
    branch: str
    repo_name: str
    pr_id: int
    pr_type: str = Field(enum=["created", "updated"])
    vcs_type: VCSTypes = VCSTypes.bitbucket.value
    confidence_score: Optional[float] = 0.7
