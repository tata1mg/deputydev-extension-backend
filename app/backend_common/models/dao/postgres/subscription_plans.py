from tortoise import fields

from .base import Base


class SubscriptionPlans(Base):
    serializable_keys = {
        "id",
        "plan_type",
        "created_at",
        "updated_at",
    }
    id = fields.IntField(primary_key=True)
    plan_type = fields.CharField(max_length=100)  # Free/Trial/Paid

    class Meta:
        table = "subscription_plans"
