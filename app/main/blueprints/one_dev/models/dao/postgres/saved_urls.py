from tortoise import fields
from tortoise.models import Model


class SavedURL(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    url = fields.TextField()
    user_team_id = fields.IntField()
    is_deleted = fields.BooleanField(default=False)
    last_indexed = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "urls"
