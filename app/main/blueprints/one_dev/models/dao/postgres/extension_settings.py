from tortoise import fields

from app.backend_common.models.dao.postgres.base import Base


class ExtensionSetting(Base):
    serializable_keys = {
        "id",
        "user_team_id",
        "client",
        "settings",
        "created_at",
        "updated_at",
    }

    id = fields.IntField(primary_key=True)
    user_team_id = fields.IntField()
    client = fields.TextField()
    settings = fields.JSONField()

    class Meta:
        table = "extension_settings"
        indexes = (("user_team_id",),)
