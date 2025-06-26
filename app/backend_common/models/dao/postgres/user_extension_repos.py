from enum import Enum
from tortoise import fields
from .base import Base

class UserExtensionRepos(Base):
    serializable_keys = {
        "id",
        "repo_name",
        "repo_id",
        "user_team_id",
        "created_at",
        "updated_at",
    }

    id = fields.BigIntField(pk=True)
    repo_name = fields.TextField()
    repo_id = fields.TextField()
    user_team_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_extension_repos"
        unique_together = (("user_team_id", "repo_id"),)
        indexes = (("user_team_id",),)

    class Columns(Enum):
        id = ("id",)
        repo_name = ("repo_name",)
        repo_id = ("repo_id",)
        user_team_id = ("user_team_id",)
        created_at = ("created_at",)
        updated_at = ("updated_at",)