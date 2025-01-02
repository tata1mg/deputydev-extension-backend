from tortoise import Model
from tortoise_wrapper.db import ModelUtilMixin, NaiveDatetimeField


class Base(Model, ModelUtilMixin):
    created_at = NaiveDatetimeField(auto_now_add=True)
    updated_at = NaiveDatetimeField(auto_now_add=True)
