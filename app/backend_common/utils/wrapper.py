import asyncio
from functools import wraps
from typing import Any, Callable

from sanic.log import logger


def exception_logger(func: Callable[..., Any]) -> Callable[..., Any]:
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as _ex:
                logger.exception(_ex)
                raise _ex

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as _ex:
                logger.exception(_ex)
                raise _ex

        return sync_wrapper
