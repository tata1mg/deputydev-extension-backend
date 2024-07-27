from enum import Enum


class TimeFormat(Enum):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))
