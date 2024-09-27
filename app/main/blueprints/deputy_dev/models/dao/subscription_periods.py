from tortoise import fields

from .base import Base


class SubscriptionPeriods(Base):
    id = fields.BigIntField(pk=True)
    subscription_id = fields.BigIntField()
    period_start = fields.DatetimeField()
    period_end = fields.DatetimeField()
    period_status = fields.CharField(max_length=100)  # active/paused/cancelled
    billing_status = fields.CharField(max_length=100)  # unbilled/billed

    class Meta:
        table = "subscription_periods"
