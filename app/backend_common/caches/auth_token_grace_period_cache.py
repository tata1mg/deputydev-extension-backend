from app.backend_common.caches.base import Base


class AuthTokenGracePeriod(Base):
    _key_prefix = "auth_token_grace_period"
    _expire_in_sec = 1800  # 30 minutes
