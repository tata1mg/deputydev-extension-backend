from datetime import datetime
import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator
from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients


class KafkaAnalyticsEventMessage(BaseModel):
    event_id : Optional[str] = None
    session_id: int
    event_type: str
    client_version: str
    client: Clients
    timestamp: datetime
    event_data: Dict[str, Any]

    # add validation to only allow event_type values in SNAKE_CASE
    @field_validator("event_type")
    def event_type_must_be_snake_case(cls, v: str) -> str:
        # Allow only CAPITAL_SNAKE_CASE (uppercase letters and underscores, cannot start/end with underscore, no consecutive underscores)
        capital_snake_case_pattern = r"^[A-Z]+(_[A-Z]+)*$"
        if not re.match(capital_snake_case_pattern, v):
            raise ValueError("event_type must be in CAPITAL_SNAKE_CASE (UPPERCASE with underscores)")
        return v
