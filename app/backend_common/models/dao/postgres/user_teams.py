from enum import Enum

from tortoise import fields

from .base import Base


class UserTeams(Base):
    id = fields.IntField(primary_key=True)
    user_id = fields.IntField()
    team_id = fields.IntField()
    role = fields.CharField(max_length=1000)
    last_pr_authored_or_reviewed_at = fields.DatetimeField()
    is_owner = fields.BooleanField()
    is_billable = fields.BooleanField()

    class Meta:
        table = "user_teams"

    class Columns(Enum):
        id = ("id",)
        user_id = ("user_id",)
        team_id = ("team_id",)
        role = ("role",)
        last_pr_authored_or_reviewed_at = ("last_pr_authored_or_reviewed_at",)
        is_owner = ("is_owner",)
        is_billable = ("is_billable",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)
