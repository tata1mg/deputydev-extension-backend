from pydantic import BaseModel


class AnalyticsData(BaseModel):
    bucket_type: str
    count: int
    step: str
    pr_score: int
    date: str
    total_reviewed: int
    total_rejected: int
