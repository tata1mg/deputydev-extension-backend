from app.backend_common.caches.base import Base


class AffirmationCache(Base):
    _key_prefix = "affirmation_message"
    _expire_in_sec = 345600  # 4 days Retention time of queue
