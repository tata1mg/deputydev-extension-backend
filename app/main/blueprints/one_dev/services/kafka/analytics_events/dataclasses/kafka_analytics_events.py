import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator

from app.backend_common.utils.dataclasses.main import Clients


class EventTypes(Enum):
    COMMENT_BOX_VIEW = "COMMENT_BOX_VIEW"
    FIX_WITH_DD = "FIX_WITH_DD"
    ACCEPTED = "ACCEPTED"
    APPLIED = "APPLIED"
    COPIED = "COPIED"
    GENERATED = "GENERATED"
    INVALID_DIFF = "INVALID_DIFF"
    TOOL_USE_REQUEST_APPROVED = "TOOL_USE_REQUEST_APPROVED"
    TOOL_USE_REQUEST_AUTO_APPROVED = "TOOL_USE_REQUEST_AUTO_APPROVED"
    TOOL_USE_REQUEST_COMPLETED = "TOOL_USE_REQUEST_COMPLETED"
    TOOL_USE_REQUEST_FAILED = "TOOL_USE_REQUEST_FAILED"
    TOOL_USE_REQUEST_INITIATED = "TOOL_USE_REQUEST_INITIATED"
    TOOL_USE_REQUEST_REJECTED = "TOOL_USE_REQUEST_REJECTED"


class KafkaAnalyticsEventMessage(BaseModel):
    event_id: Optional[str] = None
    session_id: Optional[int] = None
    event_type: EventTypes
    client_version: str
    client: Clients
    timestamp: datetime
    event_data: Dict[str, Any]

    # add validation to only allow event_type values in SNAKE_CASE
    @field_validator("event_type")
    def event_type_must_be_snake_case(cls, v: EventTypes) -> str:  # noqa: N805
        # Allow only CAPITAL_SNAKE_CASE (uppercase letters and underscores, cannot start/end with underscore, no consecutive underscores)
        capital_snake_case_pattern = r"^[A-Z]+(_[A-Z]+)*$"
        if not re.match(capital_snake_case_pattern, v.value):
            raise ValueError("event_type must be in CAPITAL_SNAKE_CASE (UPPERCASE with underscores)")
        return v
