from datetime import datetime
import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator


class KafkaErrorAnalyticsEventMessage(BaseModel):
    user_email : Optional[str] = None
    error_type: str
    repo_name : Optional[str] = None
    error_source : Optional[str] = None
    client_version: str
    timestamp: datetime
    error_data: Dict[str, Any]
    session_id: Optional[int] = None


    # add validation to only allow event_type values in SNAKE_CASE
    @field_validator("event_type")
    def event_type_must_be_snake_case(cls, v: str) -> str:
        # Allow only CAPITAL_SNAKE_CASE (uppercase letters and underscores, cannot start/end with underscore, no consecutive underscores)
        capital_snake_case_pattern = r"^[A-Z]+(_[A-Z]+)*$"
        if not re.match(capital_snake_case_pattern, v):
            raise ValueError("event_type must be in CAPITAL_SNAKE_CASE (UPPERCASE with underscores)")
        return v
