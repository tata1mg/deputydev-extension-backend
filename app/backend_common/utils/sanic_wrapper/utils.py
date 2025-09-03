import os
import sys
from functools import wraps

from app.backend_common.utils.sanic_wrapper.integrations.elasticapm import APM_CLIENT


def capture_exception(handled: bool = True):
    """Sends Exception Event to APM.

    Args:
        handled (bool, optional): whether handled or not. Defaults to True.
    """

    if not APM_CLIENT:
        return

    APM_CLIENT.capture_exception(handled=handled)


def name(obj: object) -> str:  # noqa
    return type(obj).__name__


def is_atty() -> bool:
    """
    Check if the standard output is a terminal.

    Returns:
        bool: True if the standard output is a terminal, False otherwise.
    """
    return sys.stdout and sys.stdout.isatty()


def is_local() -> bool:
    """
    Check if the application is running locally.

    Returns:
        bool: True if the application is running locally, False otherwise.
    """
    return not is_running_in_k8s()


def is_running_in_k8s() -> bool:
    """
    Check if the application is running in a Kubernetes environment.

    Returns:
        bool: True if the application is running in a Kubernetes environment,
            False otherwise.
    """
    return os.getenv("KUBERNETES_SERVICE_HOST") is not None


def legacy(reason: str | None = None):
    """Mark a function as legacy.

    This decorator does NOT modify the behavior of the decorated function in any way.
    It serves purely as a marker to indicate that the function is considered legacy,
    meaning it may be outdated, deprecated, or slated for future removal or refactoring.

    An optional reason can be provided to document why the function is considered legacy.

    Example:
        ```py
        @legacy
        def some_legacy_function(): ...


        @legacy("This function uses an outdated algorithm.")
        def another_legacy_function(): ...
        ```

    Args:
        reason (str, optional): An optional string explaining why the function is marked as legacy.
                                Defaults to None.

    Returns:
        function: The original function, unmodified.
    """  # noqa: E501

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
