from app.common.caches.base import Base


class BucketsCache(Base):
    _key_prefix = "buckets_cache"
    _expire_in_sec = 60 * 60 * 24  # 1 day
