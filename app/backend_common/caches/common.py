from app.backend_common.caches.base import Base


class CommonCache(Base):
    _key_prefix = "deputy_dev"
    _expire_in_sec = 86400 * 4  # 4 days
