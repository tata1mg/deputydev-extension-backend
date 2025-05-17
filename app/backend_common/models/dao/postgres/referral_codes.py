from tortoise import fields

from .base import Base


class ReferralCodes(Base):
    serializable_keys = {
        "id",
        "referrer_id",
        "referral_code",
        "benefits",
        "current_limit_left",
        "max_usage_limit",
        "expiration_date",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(primary_key=True)
    referrer_id = fields.BigIntField()
    referral_code = fields.CharField(max_length=100)
    benefits = fields.JSONField()
    current_limit_left = fields.IntField()
    max_usage_limit = fields.IntField()
    expiration_date = fields.DatetimeField()

    class Meta:
        table = "referral_codes"
