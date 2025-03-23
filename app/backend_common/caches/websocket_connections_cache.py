from app.backend_common.caches.base import Base


class WebsocketConnectionCache(Base):
    _key_prefix = "web_socket_connection"
    _expire_in_sec = 1800  # 30 minutes
