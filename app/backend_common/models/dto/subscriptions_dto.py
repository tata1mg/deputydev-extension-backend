from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SubscriptionData(BaseModel):
    plan_id: int
    user_team_id: int
    current_status: str
    start_date: datetime
    end_date: Optional[datetime] = None

class SubscriptionDTO(SubscriptionData):
    id: int
    created_at: datetime
    updated_at: datetime