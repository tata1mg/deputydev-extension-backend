"""Cache Wrapper Exceptions."""


class RedisWrapperError(Exception):
    """Base Redis Wrapper Exception."""


class ConfigurationError(RedisWrapperError):
    """Configuration related errors."""
