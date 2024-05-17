from enum import Enum

CHARACTER_SIZE = 2000

EXTENSION_TO_LANGUAGE = {
    "js": "javascript",
    "py": "python",
}


class ChunkFileSizeLimit(Enum):
    """
    Min and max values over here are in bytes
    """

    MIN = 10
    MAX = 240000
