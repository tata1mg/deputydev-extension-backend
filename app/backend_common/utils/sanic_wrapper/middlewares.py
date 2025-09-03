"""Sanic middlewares for Sanic."""

import time

from app.backend_common.utils.sanic_wrapper.ctx import _task_ctx
from app.backend_common.utils.sanic_wrapper.request import Request


async def add_start_time(request: Request) -> None:
    """Middleware to attach start time to request context."""

    request.ctx.started_at = int(time.perf_counter() * 1000)


async def task_ctx_factory(request: Request) -> None:
    """Middleware to set task wide context.

    - sets req id, used in log record factory
    - sets global headers, used to standardise service headers platform wide

    """
    _task_ctx.req_id = request.req_id
    _task_ctx.global_headers = request.interservice_headers
