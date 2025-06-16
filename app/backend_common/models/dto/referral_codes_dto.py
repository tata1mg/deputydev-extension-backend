from datetime import datetime

from pydantic import BaseModel


class Benifits(BaseModel):
    subscription_type: str
    subscription_expiry_timedelta: int


class ReferralCodeData(BaseModel):
    referrer_id: int
    referral_code: str
    benefits: Benifits
    current_limit_left: int
    max_usage_limit: int
    expiration_date: datetime


class ReferralCodeDTO(ReferralCodeData):
    id: int
    created_at: datetime
    updated_at: datetime
