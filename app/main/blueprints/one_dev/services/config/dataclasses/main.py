from enum import Enum


class ConfigType(Enum):
    MAIN = "MAIN"
    ESSENTIAL = "ESSENTIAL"


class ConfigConsumer(Enum):
    VSCODE_EXT = "VSCODE_EXT"
    CLI = "CLI"
    BINARY = "BINARY"
