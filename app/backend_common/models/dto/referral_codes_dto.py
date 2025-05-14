from datetime import datetime
from pydantic import BaseModel

class ReferralCodeData(BaseModel):
    referrer_id: int
    referral_code: str
    benefits: dict
    usage_limit: int
    expiration_date: datetime

class ReferralCodeDTO(ReferralCodeData):
    id: int
    created_at: datetime
    updated_at: datetime