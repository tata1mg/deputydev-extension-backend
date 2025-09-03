from tortoise import Model

from app.backend_common.utils.tortoise_wrapper.db import ModelUtilMixin, NaiveDatetimeField


class Base(Model, ModelUtilMixin):
    created_at = NaiveDatetimeField(auto_now_add=True)
    updated_at = NaiveDatetimeField(auto_now_add=True)
