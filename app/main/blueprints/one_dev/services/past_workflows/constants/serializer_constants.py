from enum import Enum


class SerializerTypes(Enum):
    PAST_SESSIONS = "PAST_SESSIONS"
    PAST_CHATS = "PAST_CHATS"


class SessionsListTypes(Enum):
    PINNED = "PINNED"
    UNPINNED = "UNPINNED"
