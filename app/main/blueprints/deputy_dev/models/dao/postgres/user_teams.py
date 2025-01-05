from tortoise import fields

from .......backend_common.models.dao.postgres.base import Base


class UserTeams(Base):
    id = fields.BigIntField(primary_key=True)
    user_id = fields.BigIntField()
    team_id = fields.BigIntField()
    role = fields.CharField(max_length=100)  # Admin/Member
    last_pr_authored_or_reviewed_at = fields.DatetimeField(null=True)  # to get active users for an org in a period
    is_owner = fields.BooleanField(default=False)
    is_billable = fields.BooleanField(default=False)

    class Meta:
        table = "user_teams"
