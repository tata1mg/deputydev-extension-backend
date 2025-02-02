from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.common.constants.constants import PromptFeatures


class SessionChatDTO(BaseModel):
    id: Optional[int] = None
    session_id: str
    prompt_type: PromptFeatures
    llm_prompt: str
    llm_response: str
    llm_model: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    response_summary: str
    user_query: str
