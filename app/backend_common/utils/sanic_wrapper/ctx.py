"""Task context management for Sanic.

Context management at different levels: task, request & application.

_Levels to this game._
"""

import types
from contextvars import ContextVar

from sanic import Sanic

from app.backend_common.utils.sanic_wrapper.request import Request


class _TaskContext:
    req_id_ctx: ContextVar[str] = ContextVar("__torpedo__req_id", default="-")
    global_headers_ctx: ContextVar[dict] = ContextVar("__torpedo__global_headers", default={})  # noqa: E501

    def __call__(self):
        return self

    @property
    def req_id(self) -> str:
        return self.req_id_ctx.get()

    @req_id.setter
    def req_id(self, req_id: str):
        self.req_id_ctx.set(req_id)

    @property
    def global_headers(self) -> dict:
        return self.global_headers_ctx.get()

    @global_headers.setter
    def global_headers(self, headers: dict) -> None:
        self.global_headers_ctx.set(headers)


_task_ctx: _TaskContext = _TaskContext()


def req_ctx() -> types.SimpleNamespace:
    """Get request context.

    Convenient utility to use request level context.

    Example:
        ```py
        from app.backend_common.utils.sanic_wrapper.ctx import req_ctx

        # set value
        req_ctx().val = ...

        # access anywhere in request
        req_ctx().val
        ```

    Returns:
        types.SimpleNamespace: Request level context.
    """
    return Request.get_current().ctx


def app_ctx() -> types.SimpleNamespace:
    """Get sanic app context.

    Convenient utility to use request level context.

    Warning:
        This is set at application level. So this will persist across requests.
        Remember this has application level scope!

    Example:
        ```py
        from app.backend_common.utils.sanic_wrapper.ctx import app_ctx

        # set value
        app_ctx().val = ...

        # access anywhere in request
        app_ctx().val
        ```

    Returns:
        types.SimpleNamespace: App level context.
    """
    return Sanic.get_app().ctx
