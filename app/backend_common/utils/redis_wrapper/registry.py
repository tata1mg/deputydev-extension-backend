from __future__ import annotations

from .constants import (
    DEFAULT_CACHE_LABEL,
    DEFAULT_REDIS_HOST,
    DEFAULT_REDIS_PORT,
    DEFAULT_TIMEOUT,
)
from .exceptions import ConfigurationError
from .utils import SingletonMeta
from .wrapper import RedisWrapper


class CacheRegistry(metaclass=SingletonMeta):
    """A singleton class to manage and register cache hosts.

    Responsible for managing and registering caches.
    """

    __slots__ = ("_caches",)

    def __init__(self) -> None:
        """Initialise a private dict for registering caches."""
        self._caches: dict[str, RedisWrapper] = {}

    def from_config(self, cache_config: dict[str, dict]):
        """Register cache hosts with the given configuration.

        This method iterates over the cache configuration dictionary
        and registers each caches.

        Args:
            cache_config (dict[str, dict]): A dict containing dicts of cache configurations.

        Example:
            ```python
            cache_config = {
                "cache1": {"LABEL": "label1", "REDIS_HOST": "localhost", "REDIS_PORT": 6379, "TIMEOUT": 10},
                "cache2": {"LABEL": "label2", "REDIS_HOST": "localhost", "REDIS_PORT": 6380, "TIMEOUT": 5},
            }
            ```

        Raises:
            ConfigurationError: If a cache host with the same label is already registered.

        """  # noqa: E501
        for _, config in cache_config.items():
            label: str = config.get("LABEL", DEFAULT_CACHE_LABEL)

            redis_wrapper: RedisWrapper = RedisWrapper(
                host=config.get("REDIS_HOST", DEFAULT_REDIS_HOST),
                port=config.get("REDIS_PORT", DEFAULT_REDIS_PORT),
                timeout=config.get("TIMEOUT", DEFAULT_TIMEOUT),
                conn_limit=config.get("CONN_LIMIT", None),
            )

            self.register(label, redis_wrapper)

    def register(self, label: str, redis_wrapper: RedisWrapper):
        """Register cache host by label.

        Args:
            label (str): Label to identify the cache.
            redis_wrapper (RedisWrapper): Redis Wrapper instance used by cache.

        Raises:
            ConfigurationError: If a cache host with the same label is already registered.

        """  # noqa: E501
        if label in self._caches:
            raise ConfigurationError(f"Cache Host with label '{label}' already registered")

        self._caches[label] = redis_wrapper

    def __getitem__(self, key: str) -> RedisWrapper:
        """Provide Dictionary like access."""
        return self._caches[key]

    def get(self, key: str) -> RedisWrapper:
        """Provide Dictionary like access."""
        return self._caches[key]

    def reset(self):
        """Clear all registered cache hosts."""
        self._caches.clear()


cache_registry = CacheRegistry()
