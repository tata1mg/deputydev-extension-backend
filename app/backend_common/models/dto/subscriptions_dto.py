from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.backend_common.constants.onboarding import SubscriptionStatus


class SubscriptionData(BaseModel):
    plan_id: int
    user_team_id: int
    current_status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime] = None


class SubscriptionDTO(SubscriptionData):
    id: int
    created_at: datetime
    updated_at: datetime
