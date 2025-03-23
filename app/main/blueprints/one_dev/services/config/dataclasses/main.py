from enum import Enum
from typing import Optional

from deputydev_core.utils.constants.enums import ConfigConsumer
from pydantic import BaseModel


class ConfigType(Enum):
    MAIN = "MAIN"
    ESSENTIAL = "ESSENTIAL"


class Architecture(Enum):
    x64 = "x64"
    ARM_64 = "arm64"


class OS(Enum):
    DARWIN = "darwin"
    LINUX = "linux"


class ConfigParams(BaseModel):
    consumer: ConfigConsumer
    arch: Optional[Architecture]
    os: Optional[OS]
