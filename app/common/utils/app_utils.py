import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

import mmh3
from sanic.log import logger
from torpedo import CONFIG, Task, TaskExecutor

from app.common.constants.constants import TimeFormat
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken


def service_client_wrapper(service_name):
    def wrapped(func):
        async def wrapper(*args):
            try:
                t1 = time.time() * 1000
                response = await func(*args)
                t2 = time.time() * 1000
                logger.debug("Time taken for {}-{} API - {} ms".format(service_name, func.__name__, t2 - t1))
                return response
            except Exception as exception:
                log_combined_exception(
                    "Unable to get response from {}-{} API".format(service_name, func.__name__),
                    exception,
                    "handled in service client wrapper",
                )

        return wrapper

    return wrapped


def log_combined_error(title, error):
    request_params = {"exception": error}
    logger.error(title, extra=request_params)
    combined_error = title + " " + error
    logger.info(combined_error)


def log_combined_exception(title, exception, meta_info: str = ""):
    error = "Exception type {} , exception {} , meta_info {}".format(type(exception), exception, str(meta_info))
    log_combined_error(title, error)


def hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def build_openai_conversation_message(system_message, user_message) -> list:
    """
    Build the conversation message list to be passed to openai.
    """
    message = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
    return message


def get_token_count(value: str) -> int:
    """
    Calculate the number of tokens in a given text.

    Parameters:
    value (str): The text for which to count the tokens.

    Returns:
    int: The number of tokens in the given text.
    """
    tiktoken_client = TikToken()
    token_count = tiktoken_client.count(text=value)
    return token_count


def get_time_difference(
    start_time: Union[datetime, str], end_time: Union[datetime, str], format: TimeFormat = TimeFormat.MINUTES.value
) -> float:
    """
    Calculate the time difference between two datetime values.

    Parameters:
    start_time (Union[datetime, str]): The start time in datetime or ISO 8601 string format.
    end_time (Union[datetime, str]): The end time in datetime or ISO 8601 string format.
    format (TimeFormat): The format for the time difference ('seconds' or 'minutes'). Default is 'minutes'.

    Returns:
    float: The time difference in the specified format.
    """
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f%z")
    if start_time.tzinfo != timezone.utc:
        start_time.astimezone(timezone.utc)

    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f%z")
    if end_time.tzinfo != timezone.utc:
        end_time.astimezone(timezone.utc)

    time_difference = (end_time - start_time).total_seconds()
    if format == TimeFormat.MINUTES.value:
        return time_difference / 60
    else:
        return time_difference


def get_ab_experiment_set(experiment_id, experiment_name):
    """
    This function required any experiment id (device id, user id, visitor id)
    and the experiment name, and it will return the control set
    it return null if experiment_id is null or last two digit not fall in any
    configure set or experiment_data is not in config
    @param experiment_id:
    @param experiment_name:
    @return:
    """

    if not experiment_id:
        return None

    experiment_data = CONFIG.config["EXPERIMENT"].get(experiment_name)

    if not experiment_data:
        return None  # Invalid experiment name

    # Calculate the last two digits of the hashed user ID
    last_two_digits = mmh3.hash(str(experiment_id)) % 100
    # Initialize the percentage range
    percent_range_start = 0

    for data in experiment_data:
        percent_range_end = percent_range_start + data["percent"]

        # Check if the last two digits fall within the current range
        if percent_range_start <= last_two_digits < percent_range_end:
            return data.get("test") or data.get("control")

        percent_range_start = percent_range_end

    return None  # Fallback if no set is assigned


async def get_task_response(tasks: List[Task]) -> Dict[str, Any]:
    response = {}
    if tasks:
        task_results = await TaskExecutor(tasks=tasks).submit()
        for idx, result in enumerate(task_results):
            if isinstance(result.result, Exception):
                logger.info("Exception while fetching task results, Details: {}".format(result.result))
            else:
                response[result.result_key] = result.result
    return response
