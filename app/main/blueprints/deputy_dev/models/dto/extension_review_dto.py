from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ExtensionReviewDTO(BaseModel):
    id: Optional[int] = None
    repo_id: int
    team_id: int
    loc: int
    reviewed_files: Dict[str, Any]
    execution_time_seconds: Optional[int] = None
    status: str
    fail_message: Optional[str] = None
    review_datetime: Optional[datetime] = None
    is_deleted: bool = False
    deletion_datetime: Optional[datetime] = None
    meta_info: Optional[dict] = None
    diff_s3_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None