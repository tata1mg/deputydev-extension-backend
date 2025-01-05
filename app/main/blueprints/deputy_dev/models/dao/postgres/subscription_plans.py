from tortoise import fields

from .......backend_common.models.dao.postgres.base import Base


class SubscriptionPlans(Base):
    id = fields.IntField(primary_key=True)
    plan_type = fields.CharField(max_length=100)  # Free/Trial/Paid

    class Meta:
        table = "subscription_plans"
