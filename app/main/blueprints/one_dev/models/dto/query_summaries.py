from datetime import datetime

from pydantic import BaseModel


class QuerySummaryData(BaseModel):
    session_id: int
    query_id: str
    summary: str


class QuerySummaryDTO(QuerySummaryData):
    id: int
    created_at: datetime
    updated_at: datetime
