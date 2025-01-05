from tortoise import fields

from .......backend_common.models.dao.postgres.base import Base


class Subscriptions(Base):
    id = fields.BigIntField(primary_key=True)
    plan_id = fields.BigIntField()
    team_id = fields.BigIntField()
    current_status = fields.CharField(max_length=100)  # active/paused/cancelled
    start_date = fields.DatetimeField()
    end_date = fields.DatetimeField()
    billable_type = fields.CharField(max_length=100)  # PR/Users – useful for applying restrictions

    class Meta:
        table = "subscriptions"
