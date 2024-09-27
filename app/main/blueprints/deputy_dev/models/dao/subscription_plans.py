from tortoise import fields

from .base import Base


class SubscriptionPlans(Base):
    id = fields.IntField(pk=True)
    plan_type = fields.CharField(max_length=100)  # Free/Trial/Paid

    class Meta:
        table = "subscription_plans"
