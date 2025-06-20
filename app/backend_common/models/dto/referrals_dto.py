from datetime import datetime

from pydantic import BaseModel


class ReferralData(BaseModel):
    referral_code_id: int
    referree_id: int


class ReferralDTO(ReferralData):
    id: int
    created_at: datetime
    updated_at: datetime
