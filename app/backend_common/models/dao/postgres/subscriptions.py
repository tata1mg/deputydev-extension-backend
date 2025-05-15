from tortoise import fields

from .base import Base


class Subscriptions(Base):
    serializable_keys = {
        "id",
        "plan_id",
        "user_team_id",
        "current_status",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(primary_key=True)
    plan_id = fields.BigIntField()
    user_team_id = fields.BigIntField()
    current_status = fields.CharField(max_length=100)  # active/paused/cancelled
    start_date = fields.DatetimeField()
    end_date = fields.DatetimeField(null=True)

    class Meta:
        table = "subscriptions"
