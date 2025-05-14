from datetime import datetime
from pydantic import BaseModel

class SubscriptionPeriodData(BaseModel):
    subscription_id: int
    period_start: datetime
    period_end: datetime
    period_status: str
    billing_status: str

class SubscriptionPeriodDTO(SubscriptionPeriodData):
    id: int
    created_at: datetime
    updated_at: datetime