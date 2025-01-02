from tortoise import fields

from .......common.models.dao.postgres.base import Base


class Integrations(Base):
    id = fields.BigIntField(primary_key=True)
    team_id = fields.BigIntField()
    client = fields.CharField(max_length=100)  # bitbucket/github/gitlab/JIRA/Confluence
    client_account_id = fields.CharField(max_length=500, null=True)
    client_username = fields.CharField(max_length=500, null=True)
    is_connected = fields.BooleanField(default=False)

    class Meta:
        table = "integrations"
