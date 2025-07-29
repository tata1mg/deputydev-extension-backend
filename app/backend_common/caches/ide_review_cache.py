from app.backend_common.caches.base import Base


class IdeReviewCache(Base):
    _key_prefix = "extension_review"
    _expire_in_sec = 86400  # 1 day
