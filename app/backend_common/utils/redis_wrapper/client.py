from __future__ import annotations

import hashlib
from functools import wraps

import numpy as np
import ujson as json

from .constants import DEFAULT_CACHE_LABEL, Encoding
from .registry import cache_registry


# FIXME: add missing docstrings
# FIXME: convert all doscrtings in accordance to google style format
class BaseServiceCache:
    """Base service cache class for managing cache operations with Redis.

    Uses the `_label` (legacy `_host`) to find cache host from `cache_registry`.
    Register cache host in the registry before using this.

    Label defaults to `DEFAULT_CACHE_LABEL` if not specified.
    It is possible that no such cache is registered, so be mindful.

    Default prefixed key
    `<service_prefix><delimiter><key_prefix><delimiter><key>`

    This behavior can be changed by overriding `prefixed_key` method.

    Attributes:
        _label (str): The "label" that maps to the cache used via `CacheRegistry`.
        _host (str): Alias for `_label`, retained for backward compatibility. Prefer using `_label`.
        _service_prefix (str): Service prefix, creates top level namespace.
        _key_prefix (str): Prefix for second level namespace.
        _delimiter (str): Delimiter used to separate cache key components.
        _expire_in_sec (int | None): Default expiration time in seconds for cache entries. This can be overridden at the method level.
        _mset_with_expire_max_keys_limit (int): Maximum number of keys allowed for batch set operations with expiration.
        _hset_with_expire_max_keys_limit (int): Maximum number of keys allowed for batch hash set operations with expiration.
        _allowed_types_for_caching (set): Set of types allowed for caching.

    Example:
        This will use the default cache
        ```python
        class CartCache(BaseServiceCache):
            _service_prefix: str = "custom"
            _key_prefix: str = "specific"
            _expire_in_sec: int = 3600  # 1 hour expiration
        ```

        Using a custom label
        ```python
        class CartCache(BaseServiceCache):
            _label = "mylabel"
        ```

    """  # noqa : E501

    _label: str = DEFAULT_CACHE_LABEL
    _host: str = _label

    _service_prefix: str = "service"
    _key_prefix: str = "base"
    _delimiter: str = ":"

    _expire_in_sec: int | None = None

    _mset_with_expire_max_keys_limit: int = 100
    _hset_with_expire_max_keys_limit: int = 100

    _allowed_types_for_caching: set = {str, int, list, tuple, float, dict, bool}

    @classmethod
    def prefixed_key(cls, key: str) -> str:
        """Return the prefixed/modified key.

        Override this method, if needed, to customise prefixed key.

        Args:
            key (str): Raw key

        Returns:
            str: Prefixed key

        """
        return f"{cls._service_prefix}{cls._delimiter}{cls._key_prefix}{cls._delimiter}{key}"  # noqa: E501

    @classmethod
    async def set(
        cls,
        key: str,
        value,
        expire=None,
        namespace: str | None = None,
        nx: bool = False,
    ):
        """Sets a key value pair.

        :param key: String
        :param value: Any (Serializable to String using str())
        :param expire: If provided, key will expire in given number of seconds. _expire_in_sec can also be set at class
        level to avoid passing it to this function everytime. If none is provided, key will live forever.
        :param namespace:
        :param nx: if set to True, set the value at key ``name`` to ``value`` only if it does not exist.
        """  # noqa : E501
        if not expire:
            expire = cls._expire_in_sec
        await cache_registry[cls._host].set(
            cls.prefixed_key(key),
            json.dumps(value),
            ex=expire,
            namespace=namespace,
            nx=nx,
        )

    @classmethod
    async def set_with_result(
        cls,
        key: str,
        value,
        expire=None,
        namespace: str | None = None,
        nx: bool = False,
    ):
        """Sets a key value pair.

        :param key: String
        :param value: Any (Serializable to String using str())
        :param expire: If provided, key will expire in given number of seconds. _expire_in_sec can also be set at class
        level to avoid passing it to this function everytime. If none is provided, key will live forever.
        :param namespace:
        :param nx: if set to True, set the value at key ``name`` to ``value`` only if it does not exist.
        """  # noqa : E501
        if not expire:
            expire = cls._expire_in_sec
        return await cache_registry[cls._host].set(
            cls.prefixed_key(key),
            json.dumps(value),
            ex=expire,
            namespace=namespace,
            nx=nx,
        )

    @classmethod
    async def publish(cls, channel: str, value):
        """Publish value at mentioned channel

        :param channel: String
        :param value: Any (Serialized to original data type which was set)
        :return: Integer - Number of subscribers that received the message
        """
        return await cache_registry[cls._host].publish(channel, json.dumps(value))

    @classmethod
    def get_pubsub(cls):
        """
        Creates and returns a PubSub instance for subscribing to channels
        and listening to published messages.

        How to use:
            1. Get a PubSub instance:
            `pubsub = BaseServiceCache.get_pubsub()`
            2. Subscribe to a channel:
            `await pubsub.subscribe("channel_name")`
            3. Retrieve messages:
            `message = await pubsub.get_message()`
        """
        return cache_registry[cls._host].get_pubsub()

    @classmethod
    async def get(cls, key: str):
        """Return the value at key, or None if the key doesn't exist.

        :param key: String
        :return: Any (Serialized to original data type which was set)
        """
        result = await cache_registry[cls._host].get(cls.prefixed_key(key))
        if result:
            result = json.loads(result)
        return result

    @classmethod
    async def incr(cls, key: str, amount: int = 1):
        """Increments the value of key by amount. If no key exists,
        the value will be initialized as amount.

        :param key: String
        :param amount: Integer
        """
        return await cache_registry[cls._host].incr(cls.prefixed_key(key), amount=amount)

    @classmethod
    async def decr(cls, key: str, amount: int = 1):
        """Decrements the value of key by amount.  If no key exists,
        the value will be initialized as 0.

        :param key: String
        :param amount: Integer
        """
        return await cache_registry[cls._host].decr(cls.prefixed_key(key), amount=amount)

    @classmethod
    async def setnx(cls, key: str, value):
        """Set a key value pair if key doesn't exist.

        :param key: String
        :param value: Any (Serializable to String using str())
        """
        await cache_registry[cls._host].setnx(cls.prefixed_key(key), json.dumps(value))

    @classmethod
    async def delete(cls, keys: list[str]):
        """Delete one or more keys specified by keys.

        :param keys: list of str
        """
        keys = list(map(lambda key: cls.prefixed_key(key), keys))
        await cache_registry[cls._host].delete(keys)

    @classmethod
    async def unlink(cls, keys: list[str]):
        """Unlink one or more keys specified by keys.

        :param keys: list of str
        """
        keys = list(map(lambda key: cls.prefixed_key(key), keys))
        await cache_registry[cls._host].unlink(keys)

    @classmethod
    async def keys(cls, pattern: str = "*"):
        """Returns a list of keys matching pattern.

        :param pattern: String
        :return: List of str
        """
        result = await cache_registry[cls._host].keys(pattern=cls.prefixed_key(pattern))
        return result

    @classmethod
    async def mset(cls, mapping: dict[str, any]):
        """Sets key/values based on a mapping. Mapping is a dictionary of
        key/value pairs. Both keys and values should be strings or types that
        can be cast to a string via str().

        :param mapping: dict
        """
        mapping = {cls.prefixed_key(k): json.dumps(v) for k, v in mapping.items()}
        await cache_registry[cls._host].mset(mapping)

    @classmethod
    async def mget(cls, keys: list[str]):
        """Returns a list of values ordered identically to keys.

        :param keys: list of str
        :return: list of any
        """
        keys = list(map(lambda key: cls.prefixed_key(key), keys))
        result = await cache_registry[cls._host].mget(keys)
        if result:
            result = list(map(lambda value: value if value else None, result))
        return result

    ###############################
    # Redis Hash related methods
    ###############################

    @classmethod
    async def hset(cls, key: str, mapping: dict[str, any]):
        """Sets a key value pair within hash key,
        mapping accepts a dict of key/value pairs that that will be
        added to hash key.

        Returns the number of fields that were added.
        :param key: String
        :param mapping: dict {key: String, value: Any (Serializable to String using str())}
        """  # noqa : E501
        mapping = {k: json.dumps(v) for k, v in mapping.items()}
        await cache_registry[cls._host].hset(cls.prefixed_key(key), mapping)

    # FIXME: raise custom exception
    @classmethod
    async def hset_with_expire(cls, key: str, mapping: dict[str, any], expire=None):
        if not expire:
            expire = cls._expire_in_sec
        if len(mapping.keys()) > cls._hset_with_expire_max_keys_limit:
            raise Exception(
                f"Please use batch processing for keys count > {cls._hset_with_expire_max_keys_limit}"  # noqa : E501
            )
        mapping = {k: json.dumps(v) for k, v in mapping.items()}
        await cache_registry[cls._host].hset_with_expire(cls.prefixed_key(key), mapping, expire)

    @classmethod
    async def hget(cls, key: str, field: str):
        """Return the value of filed within the hash key.

        :param key: String
        :param field: String
        :return: Any (Serialized to original data type which was set)
        """
        result = await cache_registry[cls._host].hget(cls.prefixed_key(key), field)
        if result:
            result = json.loads(result)
        return result

    @classmethod
    async def hmget(cls, key, fields):
        """
        Return the value of fields within the hash key
        similar to hget but returns multiple values.
        :param key: String
        :param fields: array
        """
        result = await cache_registry[cls._host].hmget(cls.prefixed_key(key), fields)
        return result

    @classmethod
    async def hdel(cls, key: str, fields: list[str]):
        """Delete one or more fields from hash key.

        :param key: String
        :param fields: list of str
        """
        await cache_registry[cls._host].hdel(cls.prefixed_key(key), fields)

    @classmethod
    async def hgetall(cls, key: str):
        """Return a Python dict of the hash's field/value pairs.

        :param key: String
        :return: dict {key: String, value: Any (Serialized to original data type which was set)}
        """  # noqa : E501
        result = await cache_registry[cls._host].hgetall(cls.prefixed_key(key))
        if result:
            result = {k: json.loads(v) for k, v in result.items()}
        return result

    @classmethod
    async def hincrby(cls, key: str, field: str, value: int = 1):
        """Increment the value of field in hash key by amount.

        :param key: String
        :param field: String
        :param value: Integer
        """
        await cache_registry[cls._host].hincrby(cls.prefixed_key(key), field, value)

    @classmethod
    async def hkeys(cls, key: str):
        """Return the list of keys within hash key.

        :param key: String
        :return: list of str
        """
        return await cache_registry[cls._host].hkeys(cls.prefixed_key(key))

    ###############################
    # Redis List related methods
    ###############################

    @classmethod
    async def lpush(cls, key: str, values: list[any]):
        """Push values onto the head of the list key.

        :param key: String
        :param values: list of any
        """
        await cache_registry[cls._host].lpush(cls.prefixed_key(key), values)

    @classmethod
    async def rpush(cls, key: str, values: list[any]):
        """Push values onto the tail of the list key.

        :param key:  String
        :param values: list of any
        """
        await cache_registry[cls._host].rpush(cls.prefixed_key(key), values)

    @classmethod
    async def lpop(cls, key: str):
        """Remove and return the first item of the list key.

        :param key: String
        :return: any
        """
        result = await cache_registry[cls._host].lpop(cls.prefixed_key(key))
        return result

    @classmethod
    async def lrange(cls, key: str, start: int = 0, end: int = -1):
        """Return a slice of the list key between position start and end.

        start and end can be negative numbers just like
        Python slicing notation
        :param key: String
        :param start: int
        :param end: int
        :return: list of any
        """
        result = await cache_registry[cls._host].lrange(cls.prefixed_key(key), start, end)
        return result

    @classmethod
    async def delete_by_prefix(cls, prefix: str):
        result = await cache_registry[cls._host].delete_by_prefix(cls.prefixed_key(prefix))
        return result

    @classmethod
    async def members_in_set(cls, key: str, namespace: str | None = None):
        result = await cache_registry[cls._host].smembers(cls.prefixed_key(key), namespace=namespace)
        return result

    @classmethod
    async def is_value_in_set(cls, key: str, value, namespace: str | None = None):
        result = await cache_registry[cls._host].sismember(cls.prefixed_key(key), value, namespace=namespace)
        return result

    @classmethod
    async def mset_with_expire(cls, mapping: dict[str, any], expire=None):
        """Drop-in replacement: store embeddings safely (np.ndarray → bytes, others → JSON)."""
        if not expire:
            expire = cls._expire_in_sec

        if len(mapping.keys()) > cls._mset_with_expire_max_keys_limit:
            raise Exception(f"Please use batch processing for keys count > {cls._mset_with_expire_max_keys_limit}")

        serialized = {}
        for k, v in mapping.items():
            if isinstance(v, np.ndarray):
                v = v.astype(np.float32).tobytes()
            else:
                if v is not None:
                    v = json.dumps(v)
                else:
                    continue  # skip None values
            serialized[cls.prefixed_key(k)] = v

        await cache_registry[cls._host].mset_with_expire(serialized, expire)

    @classmethod
    async def expire_many(cls, keys: list[str], expire: int):
        """Set expire time for a given list of keys.
        Uses pipelining for better performance.

        :param keys: list of str
        :param expire: integer ( expiry time in seconds )
        :return: 1 = key found and expiry set for the key
                 0 = expiry time not set because key not found
        """
        keys = list(map(lambda key: cls.prefixed_key(key), keys))
        result = await cache_registry[cls._host].expire_many(keys, expire)
        return result

    # FIXME: raise custom exception
    @classmethod
    async def mset_with_varying_ttl(cls, items: list[tuple[str, any, int]]):
        if len(items) > cls._mset_with_expire_max_keys_limit:
            raise Exception(
                f"Please use batch processing for keys count > {cls._mset_with_expire_max_keys_limit}"  # noqa : E501
            )
        items = [(cls.prefixed_key(k), json.dumps(v), ex if ex else cls._expire_in_sec) for k, v, ex in items]
        await cache_registry[cls._host].mset_with_varying_ttl(items)

    @classmethod
    async def eval(cls, script, numkeys, *keys_and_args):
        result = await cache_registry[cls._host].eval(script, numkeys, *keys_and_args)
        return result

    ###############################
    # Redis Sorted Set related methods
    ###############################

    @classmethod
    async def zadd(cls, key: str, element):
        """Add one or more member to sorted set & update score if key already exists.

        :param element: element(s) with score
        :param key: String
        :return: any
        """
        result = await cache_registry[cls._host].zadd(cls.prefixed_key(key), element)
        return result

    @classmethod
    async def zpopmin(cls, key: str, count=None):
        """Remove and return the count number of members with minimum score.

        :param key: String
        :count: integer
        :return: min score elements from sorted redis
        """
        result = await cache_registry[cls._host].zpopmin(cls.prefixed_key(key), count)
        return result

    @classmethod
    async def zrange(cls, key: str, limit, offset, withscores=False):
        """Retrieve a range of members from a sorted set.

        :param limit: starting index of the range to retrieve
        :param offset: ending index of the range to retrieve
        :param key: name of the sorted set
        :return: min score element from sorted redis
        """
        result = await cache_registry[cls._host].zrange(cls.prefixed_key(key), limit, offset, withscores=withscores)
        return result

    @classmethod
    async def zpopmax(cls, key: str, count=None):
        """Remove and return the count number of members with maximum score.

        :param key: String
        :param count: integer
        :return: max score elements from sorted redis
        """
        result = await cache_registry[cls._host].zpopmax(cls.prefixed_key(key), count=count)
        return result

    @classmethod
    async def zrevrangebyscore(cls, key: str, max, min, start=0, num=1, withscores=False):
        """Remove and return the count number of members with maximum score in a given interval.

        :param key: name of the key
        :param min: min interval score
        :param max: max interval score
        :param withscores: return members with scores
        :param start: offset
        :param num: limit
        :param withscores: return members with scores
        : Return a range of values from the sorted set ``key`` with scores
        between ``min`` and ``max`` in descending order.
        """  # noqa: E501
        result = await cache_registry[cls._host].zrevrangebyscore(
            cls.prefixed_key(key), max, min, start=start, num=num, withscores=withscores
        )
        return result

    ###############################
    # Redis Set related methods
    ###############################

    @classmethod
    async def sadd(cls, key: str, *args):
        """Add one or more member to set.

        :param args: element(s)
        :param key: String
        :return: any
        """
        for value in args:
            await cache_registry[cls._host].sadd(cls.prefixed_key(key), value)

    @classmethod
    async def spop(cls, key: str, count=None):
        """Remove and return the count number of members with maximum score.

        :param key: String
        :param count: integer
        :return: elements from set redis
        """
        result = await cache_registry[cls._host].spop(cls.prefixed_key(key), count)
        return result

    @classmethod
    async def expire(cls, key: str, expire):
        """Set expire time for a given key.

        :param key: String
        :param expire: integer ( expiry time in seconds )
        :return: 1 = key found and expiry set for the key
                 0 = expiry time not set because key not found
        """
        result = await cache_registry[cls._host].expire(cls.prefixed_key(key), expire)
        return result

    @classmethod
    async def is_key_exist(cls, key: str):
        """Check if a single key exists in redis cache.

        :param key: String
        :return: 1 = key exists in cache
                 0 = key does not exist in cache
        """
        result = await cache_registry[cls._host].exists(cls.prefixed_key(key))
        return result

    ###############################
    # Custom Utils
    ###############################

    # NOTE: a bit problematic as it uses a different prefix key than rest of the methods
    # this can lead to bugs or create confusion.
    # FIXME: add detailed docstring
    @classmethod
    def redis_cache_decorator(cls, name_space: str = "", expire_time: int = 0):
        def wrapped(func):
            @wraps(func)
            async def apply_cache(*args, **kwargs):
                ##########################################
                # Prepare pos arguments for cache key
                ##########################################

                _args = ""
                if args and len(args) > 0:
                    new_args = []
                    for arg in args[1:]:
                        if type(arg) in cls._allowed_types_for_caching:
                            if isinstance(arg, dict):
                                new_args.append(json.dumps(arg, sort_keys=True))
                            else:
                                new_args.append(arg)
                    _args = str(new_args)

                ##########################################
                # Prepare keyword arguments for cache key
                ##########################################

                _kwargs = {}
                for key in kwargs:
                    if type(kwargs[key]) in cls._allowed_types_for_caching:
                        _kwargs[key] = kwargs[key]

                ##########################################
                # Generate cache key
                ##########################################
                redis_key = json.dumps(
                    {
                        "func": func.__name__,
                        "args": _args,
                        "kwargs": _kwargs,
                    },
                    sort_keys=True,
                )

                # Calculate the digest of the cache key
                digest_key = hashlib.md5(redis_key.encode(Encoding.UTF8)).hexdigest()  # noqa: S324 # acceptable use
                _key = cls._get_key(name_space, digest_key)

                # Check if the cache exists
                result = await cls.get(key=_key)

                if result:
                    return json.loads(result)

                # If not cached, call the original function
                result = await func(*args, **kwargs)

                # Cache the result
                await cls.set(key=_key, value=json.dumps(result), expire=expire_time)
                return result

            return apply_cache

        return wrapped

    # FIXME: creates confusion, move inside the decorator above
    @staticmethod
    def _get_key(namespace, key):
        return f"{namespace}:{key}"


# alias
RedisCache = BaseServiceCache
