from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExtensionFeedbacksData(BaseModel):
    query_id: int
    feedback: str


class ExtensionFeedbacksDTO(ExtensionFeedbacksData):
    id: int
    created_at: datetime
    updated_at: datetime
