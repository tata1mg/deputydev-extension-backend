from app.backend_common.utils.redis_wrapper.client import RedisCache
from app.backend_common.utils.sanic_wrapper import CONFIG


class EmbeddingCache(RedisCache):
    """Cache class specifically for storing embeddings.

    Uses a separate Redis instance optimized for large binary data storage.
    This instance should be configured with more memory compared to the general cache.
    """

    _service_prefix = "genai"
    _label = CONFIG.config["REDIS_CACHE_HOSTS"]["embedding"]["LABEL"]
    _host = _label  # Backward compatibility
    _key_prefix = "deputy_dev"  # Keep same prefix as CommonCache for backward compatibility
    _expire_in_sec = 86400 * 7  # 7 days for embeddings
