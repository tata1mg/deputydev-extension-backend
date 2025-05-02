import asyncio
from functools import wraps

from sanic.log import logger
from torpedo import Request, send_response

from app.backend_common.utils.headers import Headers


def http_v4_wrapper(func):
    @wraps(func)
    async def wrapper(request: Request):
        headers = Headers(request.headers)
        response = await func(request, headers)
        return send_response(response.model_dump())

    return wrapper


def exception_logger(func):
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as _ex:
                logger.exception(_ex)
                raise _ex

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as _ex:
                logger.exception(_ex)
                raise _ex

        return sync_wrapper


def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        import time

        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start_time} seconds")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import time

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start_time} seconds")
        return result

    return wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
