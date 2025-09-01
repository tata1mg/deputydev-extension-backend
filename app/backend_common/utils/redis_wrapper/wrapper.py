# ruff : noqa : D102
# This rule is ignored because methods here mostly
# call the same methods from redis.asyncio.Redis class
# and do not add much functionality on top of it
# except modifying the key or providing defaults args.
# Ideally newer methods added here should add a docstring tho.

from __future__ import annotations

import redis.asyncio as redis

from .constants import RedisProtocols


class RedisWrapper:
    """Wrapper class composing redis.Redis.

    Defines methods with modified key or defaults to args.

    Example:
        ```python
        from app.backend_common.utils.redis_wrapper.wrapper import RedisWrapper

        rw = RedisWrapper(host="localhost", port=6379)
        await rw.incr("my_counter")
        ```
        # or pass a custom already instantiated redis instance.

        ```python
        import redis.asyncio as redis

        r = redis.Redis(host='localhost', port=6379, ...)
        rw = RedisWrapper(redis=r)

        ```

    """

    __slots__ = (
        "_host",
        "_port",
        "_timeout",
        "_conn_limit",
        "_redis",
    )

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout: int | None = None,
        redis: redis.Redis | None = None,
        conn_limit: int | None = None,
    ) -> None:
        """Initialise the wrapper class with a redis.Redis instance.

        Creates a new connection from provided configuration or uses an already
        instantiated one.

        Args:
            host (str | None, optional): Redis server host. Defaults to None.
            port (int | None, optional): Port on which Redis Server is running. Defaults to None.
            timeout (int | None, optional): Global timeout for redis commands. Defaults to None.
            redis (redis.Redis | None, optional): Already instantiated redis connection. Defaults to None.

        """  # noqa: E501
        self._host = host
        self._port = port
        self._timeout = timeout
        self._conn_limit = conn_limit

        if redis:
            self._redis: redis.Redis = redis
        else:
            self._redis: redis.Redis = self._get_redis()

    def _get_redis(self) -> redis.Redis:
        """Override this method to customise redis.Redis connection creation.

        Preffered approach is to pass a redis.Redis instance to the constructor.

        Returns
        -------
            redis.Redis: Redis Interface

        """

        if self._conn_limit:
            # use BlockingConnectionPool

            pool = redis.BlockingConnectionPool(
                host=self._host,
                port=self._port,
                decode_responses=True,
                socket_timeout=self._timeout,
                max_connections=self._conn_limit,
                protocol=int(RedisProtocols.RESP2),
            )

            return redis.Redis.from_pool(connection_pool=pool)

        return redis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=True,
            socket_timeout=self._timeout,
            protocol=int(RedisProtocols.RESP2),
        )

    @staticmethod
    def _get_key(namespace: str, key: str) -> str:
        """Append namespace to provided key."""
        return f"{namespace}:{key}"

    async def sadd(self, key: str, value, namespace: str | None = None):
        if namespace is not None:
            key = self._get_key(namespace, key)
        await self._redis.sadd(key, value)

    async def set(
        self,
        key: str,
        value,
        ex=None,
        namespace: str | None = None,
        nx: bool = False,
    ):
        if namespace is not None:
            key = self._get_key(namespace, key)
        return await self._redis.set(key, value, ex=ex, nx=nx)

    async def get(self, key: str, namespace: str | None = None):
        if namespace is not None:
            key = self._get_key(namespace, key)
        return await self._redis.get(key)

    async def incr(self, key: str, amount=1):
        # Set a redis key and increment the value by one
        return await self._redis.incr(key, amount)

    async def increment_by_value(self, key: str, value: int):
        await self._redis.incrby(key, value)

    async def decr(self, key: str, amount=1):
        # Set a redis key and increment the value by one
        return await self._redis.decr(key, amount)

    async def decrement_by_value(self, key: str, value: int):
        await self._redis.decrby(key, value)

    async def setnx(self, key: str, value):
        return await self._redis.setnx(key, value)

    async def delete(self, keys):
        await self._redis.delete(*keys)

    async def unlink(self, keys):
        await self._redis.unlink(*keys)

    async def mset(self, mapping: dict):
        await self._redis.mset(mapping)

    async def mget(self, keys):
        return await self._redis.mget(keys)

    async def hset(self, key: str, mapping):
        await self._redis.hset(key, mapping=mapping)

    async def hset_with_expire(self, key: str, mapping, expire=None):
        pipeline = self._redis.pipeline()
        pipeline.hset(key, mapping=mapping)
        if expire is not None:
            pipeline.expire(key, expire)
        await pipeline.execute()

    async def hget(self, key: str, field):
        return await self._redis.hget(key, field)

    async def hmget(self, key, fields):
        return await self._redis.hmget(key, fields)

    async def hdel(self, key: str, fields):
        if key is not None:
            await self._redis.hdel(key, *fields)

    async def hgetall(self, key: str):
        return await self._redis.hgetall(key)

    async def hincrby(self, key: str, field, value: int = 1):
        return await self._redis.hincrby(key, field, value)

    async def hkeys(self, key: str):
        return await self._redis.hkeys(key)

    async def lpush(self, key: str, values):
        return await self._redis.lpush(key, *values)

    async def rpush(self, key: str, values):
        return await self._redis.rpush(key, *values)

    async def lpop(self, key: str):
        return await self._redis.lpop(key)

    async def brpop(self, keys, timeout=0):
        return await self._redis.brpop(keys, timeout=timeout)

    async def lrange(self, key: str, start, stop):
        return await self._redis.lrange(key, start, stop)

    async def clear_namespace(self, namespace: str) -> int:
        pattern = namespace + "*"
        return await self._delete_by_pattern(pattern)

    async def delete_by_prefix(self, prefix: str):
        pattern = f"{prefix}*"
        return await self._delete_by_pattern(pattern)

    async def _delete_by_pattern(self, pattern: str) -> int:
        if not pattern:
            return 0

        _keys = await self._redis.keys(pattern)
        if _keys:
            await self._redis.delete(*_keys)
        return len(_keys)

    async def keys(self, pattern: str) -> list[str]:
        """Retrieve all keys in Redis that match the given pattern.

        Args:
        ----
            pattern (str): The pattern to match keys against.

        Returns:
        -------
            list[str]: A list of Redis keys that match the given pattern.

        """
        if pattern:
            return await self._redis.keys(pattern + "*")
        return []

    async def smembers(self, key: str, namespace: str | None = None):
        if namespace is not None:
            key = self._get_key(namespace, key)

        return await self._redis.smembers(key)

    async def sismember(self, key: str, value, namespace: str | None = None):
        if namespace is not None:
            key = self._get_key(namespace, key)
        return await self._redis.sismember(key, value)

    async def mset_with_expire(self, mapping: dict, ex=None):
        pipeline = self._redis.pipeline()
        for key, value in mapping.items():
            pipeline.set(key, value, ex=ex)
        await pipeline.execute()

    async def mset_with_varying_ttl(self, items: list[tuple]):
        pipeline = self._redis.pipeline()
        for key, value, ex in items:
            pipeline.set(key, value, ex=ex)
        await pipeline.execute()

    async def eval(self, script, numkeys, *keys_and_args):
        return await self._redis.eval(script, numkeys, *keys_and_args)

    async def expire(self, key: str, timeout):
        await self._redis.expire(key, timeout)

    async def zadd(self, key: str, value):
        return await self._redis.zadd(key, value)

    async def zpopmin(self, key: str, count=None):
        return await self._redis.zpopmin(key, count)

    async def zrange(self, key: str, limit, offset, withscores=False):
        return await self._redis.zrange(key, limit, offset, withscores=withscores)

    async def zrevrangebyscore(
        self,
        key: str,
        max,
        min,
        start: int | None = 0,
        num: int | None = 1,
        withscores: bool = False,
    ):
        return await self._redis.zrevrangebyscore(
            key,
            max,
            min,
            start=start,
            num=num,
            withscores=withscores,
        )

    async def zpopmax(self, key: str, count=None):
        return await self._redis.zpopmax(key, count)

    async def spop(self, key: str, count=None):
        return await self._redis.spop(key, count)

    async def exists(self, *keys):
        return await self._redis.exists(*keys)

    async def publish(self, channel: str, value):
        return await self._redis.publish(channel, value)

    def get_pubsub(self):
        pubsub = self._redis.pubsub()
        return pubsub
