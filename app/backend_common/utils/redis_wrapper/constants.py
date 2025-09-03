from enum import Enum


class Encoding:
    """Encoding values."""

    UTF8 = "utf-8"


DEFAULT_CACHE_LABEL = "global"
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_TIMEOUT = 2  # 2 sec


class RedisProtocols(int, Enum):
    RESP2 = 2

    # WARNING: only to be used with latest version of redis server!
    RESP3 = 3
