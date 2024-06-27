from datetime import datetime, timezone
from functools import wraps

from sanic.log import logger

from app.common.constants.constants import TimeFormat
from app.common.utils.app_utils import get_time_difference


def log_time(func):
    """
    Decorator to log the execution time of methods.

    Args:
        func: The asynchronous function to be decorated.

    Returns:
        The decorated function with logging.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        """
        Wrapper function to log the start time, end time, and any exceptions raised during execution.

        Args:
            args: Positional arguments for the decorated function.
            kwargs: Keyword arguments for the decorated function.

        Returns:
            The result of the decorated function.

        Raises:
            Exception: Any exception raised by the decorated function.
        """

        # Currently we are checking request_id, if it is present in kwargs or not, it's not an ideal way to attach
        # request_id but requests received in background doesn't have request_id which makes finding log traces
        # difficult. This is a temporary check where we are checking if we are receiving request_id in payload or not and then
        # adding it into logs, will have to find a better alternative
        request_id = None
        start_time = datetime.now(timezone.utc)
        # Format the datetime as per the specified format
        formatted_start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        if kwargs["data"]["request_id"]:
            request_id = kwargs["data"]["request_id"]
        start_message = f"Start: {func.__name__} at {formatted_start_time}"
        if request_id:
            start_message = start_message + f", for request ID - {request_id}"
        logger.info(start_message)

        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            formatted_end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            exception_message = f"Error: {func.__name__} at {formatted_end_time}"
            if request_id:
                exception_message = exception_message + f", for request ID - {request_id}"
            exception_message = exception_message + f" - {e}"
            logger.error(exception_message)
            raise e

        end_time = datetime.now(timezone.utc)
        formatted_end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        end_message = f"End: {func.__name__} at {formatted_end_time} - Elapsed: {get_time_difference(start_time, end_time, TimeFormat.SECONDS.value):6f} seconds"
        if request_id:
            end_message = end_message + f", for request ID - {request_id}"
        logger.info(end_message)

        return result

    return wrapper
