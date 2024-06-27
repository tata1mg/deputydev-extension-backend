from app.common.caches.base import Base


class Jiva(Base):
    _key_prefix = "jiva"
    _expire_in_sec = 1296000  # 15 days 15*24*60*60 = 1296000
