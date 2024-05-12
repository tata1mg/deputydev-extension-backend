from enum import Enum


class CacheExpiry(Enum):
    """
    Cache Expiry
    """

    DEFAULT = 5400  # 1.5 hrs
    DEFAULT_LONG = 604800  # 1 week
    DEFAULT_SHORT = 600  # 10 min
