from redis_wrapper.client import RedisCache
from torpedo import CONFIG


class Base(RedisCache):
    _service_prefix = "genai"
    _host = CONFIG.config["REDIS_CACHE_HOSTS"]["genai"]["LABEL"]
    _key_prefix = ""
