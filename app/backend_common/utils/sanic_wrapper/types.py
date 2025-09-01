import typing as t
from enum import Enum

from sanic.models.handler_types import (
    ErrorMiddlewareType,
    ListenerType,
    MiddlewareType,
    SignalHandler,
)

ListenerEventTuple = t.Tuple[ListenerType, str]
MiddlewaresTargetTuple = t.Tuple[MiddlewareType, str]
HandlerExceptionTuple = t.Tuple[ErrorMiddlewareType, t.Union[Exception, t.Sequence[Exception]]]
SignalHandlerTuple = t.Tuple[SignalHandler, t.Union[str, Enum]]


class ResponseDict(t.TypedDict):
    data: dict
    is_success: bool
    status_code: int
    meta: t.NotRequired[t.Any]


class ErrorResponseDict(t.TypedDict):
    error: dict
    is_success: bool
    status_code: int
    meta: t.NotRequired[t.Any]
    error_code: int
