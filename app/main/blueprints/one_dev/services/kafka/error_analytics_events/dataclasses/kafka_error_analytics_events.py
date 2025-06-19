import re
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator


class KafkaErrorAnalyticsEventMessage(BaseModel):
    error_id: Optional[str] = None
    user_email: Optional[str] = None
    error_type: str
    repo_name: Optional[str] = None
    error_source: Optional[str] = None
    stack_trace: Optional[str] = None
    user_system_info: Optional[Dict[str, Any]] = None
    client_version: str
    timestamp: datetime
    error_data: Dict[str, Any]
    session_id: Optional[int] = None

    # add validation to only allow error_type values in SNAKE_CASE
    @field_validator("error_type")
    def error_type_must_be_snake_case(cls, v: str) -> str:  # noqa: N805
        # Allow only CAPITAL_SNAKE_CASE (uppercase letters and underscores, cannot start/end with underscore, no consecutive underscores)
        capital_snake_case_pattern = r"^[A-Z]+(_[A-Z]+)*$"
        if not re.match(capital_snake_case_pattern, v):
            raise ValueError("error_type must be in CAPITAL_SNAKE_CASE (UPPERCASE with underscores)")
        return v
