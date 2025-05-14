from tortoise import fields

from .base import Base


class SubscriptionPeriods(Base):
    serializable_keys = {
        "id",
        "subscription_id",
        "period_start",
        "period_end",
        "period_status",
        "billing_status",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(primary_key=True)
    subscription_id = fields.BigIntField()
    period_start = fields.DatetimeField()
    period_end = fields.DatetimeField()
    period_status = fields.CharField(max_length=100)  # active/paused/cancelled
    billing_status = fields.CharField(max_length=100)  # unbilled/billed

    class Meta:
        table = "subscription_periods"
