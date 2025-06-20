from datetime import datetime

from pydantic import BaseModel


class SubscriptionPlanData(BaseModel):
    plan_type: str


class SubscriptionPlanDTO(SubscriptionPlanData):
    id: int
    created_at: datetime
    updated_at: datetime
