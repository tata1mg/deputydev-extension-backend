from app.common.caches.base import Base


class DeputyDevCache(Base):
    _key_prefix = "deputy_dev"
    _expire_in_sec = 604800  # 1 week
