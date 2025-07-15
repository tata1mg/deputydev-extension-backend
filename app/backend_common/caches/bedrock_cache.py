from app.backend_common.caches.base import Base


class BedrockCache(Base):
    _key_prefix = "bedrock_cache"
    _expire_in_sec = 86400 * 4  # 4 days
