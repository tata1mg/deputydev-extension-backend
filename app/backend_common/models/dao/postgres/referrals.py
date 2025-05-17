from tortoise import fields

from .base import Base


class Referrals(Base):
    serializable_keys = {
        "id",
        "referral_code_id",
        "referree_id",
        "created_at",
        "updated_at",
    }
    id = fields.BigIntField(primary_key=True)
    referral_code_id = fields.BigIntField()
    referree_id = fields.BigIntField()

    class Meta:
        table = "referrals"
