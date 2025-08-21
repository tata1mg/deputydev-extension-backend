from enum import StrEnum


class MiddlewareLocation(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"


class ListenerEvent(StrEnum):
    AFTER_SERVER_START = "after_server_start"
    BEFORE_SERVER_START = "before_server_start"
    BEFORE_SERVER_STOP = "before_server_stop"
    AFTER_SERVER_STOP = "after_server_stop"


ListenerEventTypes = ListenerEvent
"""Alias for backward compatibility."""
