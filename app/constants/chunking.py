from enum import Enum

EXTENSION_TO_LANGUAGE = {
    "js": "javascript",
    "py": "python",
}


class ChunkFileSizeLimit(Enum):
    """
    Min and max values over here are in bytes
    """

    MIN = 10
    MAX = 260000
