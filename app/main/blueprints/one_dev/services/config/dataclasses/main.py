from enum import Enum

from deputydev_core.utils.constants.enums import ConfigConsumer
from pydantic import BaseModel


class ConfigType(Enum):
    MAIN = "MAIN"
    ESSENTIAL = "ESSENTIAL"


class Architecture(Enum):
    x86_64 = "x86_64"
    ARM_64 = "arm64"


class OS(Enum):
    DARWIN = "Darwin"
    LINUX = "Linux"


class ConfigParams(BaseModel):
    consumer: ConfigConsumer
    arch: Architecture
    os: OS
