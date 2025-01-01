# wrapper to get session ID from headers or add one if not present
from functools import wraps
from uuid import uuid4

from torpedo import Request


def ensure_session_id(func):
    """
    Wrapper to ensure a session ID is present in the request headers.
    """

    @wraps(func)
    async def wrapper(_request: Request, **kwargs):
        # Check if the session ID is present in the headers
        session_id = _request.headers.get("X-Session-ID")
        if not session_id:
            # Add a session ID to the headers
            session_id = uuid4().hex
            _request.headers["X-Session-ID"] = session_id
        # Proceed to the wrapped function
        return await func(_request, **kwargs)

    return wrapper
