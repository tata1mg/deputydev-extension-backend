from redis_wrapper.client import RedisCache
from torpedo import CONFIG

from app.constants import CacheExpiry

# from app.json_encoder import jsonable_encoder


class Base(RedisCache):
    _service_prefix = "genai"
    _host = CONFIG.config["REDIS_CACHE_HOSTS"]["genai"]["LABEL"]
    _key_prefix = ""
    _expire_in_sec = CacheExpiry.DEFAULT
