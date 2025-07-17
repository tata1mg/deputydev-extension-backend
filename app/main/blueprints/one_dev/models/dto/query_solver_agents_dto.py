from datetime import datetime
from typing import List

from pydantic import BaseModel


class QuerySolverAgentsData(BaseModel):
    name: str
    agent_enum: str
    description: str
    prompt_intent: str
    allowed_first_party_tools: List[str]
    status: str = "ACTIVE"


class QuerySolverAgentsDTO(QuerySolverAgentsData):
    id: int
    created_at: datetime
    updated_at: datetime
