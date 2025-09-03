import hashlib
import time
from datetime import datetime
from typing import Any, Callable, Dict, List

import mmh3
from deputydev_core.services.tiktoken import TikToken
from sanic.log import logger

from app.backend_common.utils.sanic_wrapper import CONFIG, Task, TaskExecutor


def service_client_wrapper(service_name: str) -> Callable[..., Any]:
    def wrapped(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                t1 = time.time() * 1000
                response = await func(*args, **kwargs)
                t2 = time.time() * 1000
                logger.debug("Time taken for {}-{} API - {} ms".format(service_name, func.__name__, t2 - t1))
                return response
            except Exception as exception:  # noqa: BLE001
                log_combined_exception(
                    "Unable to get response from {}-{} API".format(service_name, func.__name__),
                    exception,
                    "handled in service client wrapper",
                )

        return wrapper

    return wrapped


def log_combined_error(title: str, error: str) -> None:
    request_params = {"exception": error}
    logger.error(title, extra=request_params)
    combined_error = title + " " + error
    logger.info(combined_error)


def log_combined_exception(title: str, exception: Exception, meta_info: str = "") -> None:
    error = "Exception type {} , exception {} , meta_info {}".format(type(exception), exception, str(meta_info))
    log_combined_error(title, error)


def build_openai_conversation_message(system_message: str, user_message: str) -> List[Dict[str, str]]:
    """
    Build the conversation message list to be passed to openai.
    """
    message = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
    return message


def get_foundation_model_name() -> str:
    model_config = CONFIG.config.get("SCRIT_MODEL")
    model = model_config["MODEL"]
    return model


TIKTOKEN_CLIENT = TikToken()


def get_token_count(value: str) -> int:
    """
    Calculate the number of tokens in a given text.

    Parameters:
    value (str): The text for which to count the tokens.

    Returns:
    int: The number of tokens in the given text.
    """
    token_count = TIKTOKEN_CLIENT.count(text=value, model=get_foundation_model_name())
    return token_count


def get_ab_experiment_set(experiment_id: str, experiment_name: str) -> Dict[str, Any] | None:
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


async def get_task_response(tasks: List[Task], suppress_exception: bool = True) -> Dict[str, Any]:
    response = {}
    if tasks:
        task_results = await TaskExecutor(tasks=tasks).submit()
        for idx, result in enumerate(task_results):
            if isinstance(result.result, Exception):
                logger.info("Exception while fetching task results, Details: {}".format(result.result))
                if not suppress_exception:
                    raise result.result
            else:
                response[result.result_key] = result.result
    return response


def convert_to_datetime(iso_string: str) -> datetime:
    """
    Convert an ISO 8601 formatted string to a datetime object.

    Args:
        iso_string (str): The ISO 8601 formatted string.

    Returns:
        datetime: The corresponding datetime object.
    """
    if "UTC" in iso_string:
        iso_string = iso_string.replace(" UTC", "+00:00")  # Gitlab created at example: 2024-09-16 07:03:03 UTC
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def get_vcs_repo_name_slug(value: str) -> str:
    """
    extracts repo slug from the full name passed to it

    Args:
        value (str): string from which the value needs to be extracted.

    Returns:
        datetime: The corresponding datetime object.
    """
    parts = value.split("/")
    return parts[-1]


def get_gitlab_workspace_slug(value: str) -> str:
    """
    extracts gitlab workspace slug from the full name passed to it

    Args:
        value (str): string from which the value needs to be extracted.

    Returns:
        datetime: The corresponding datetime object.
    """
    parts = value.split("/")
    return parts[0]


def name_to_slug(input_str: str) -> str:
    """
    Converts a name to a slug.

    Args:
        input_str (str): Name passed as argument.

    Returns:
        str: The corresponding slug.
    """
    lower_str = input_str.lower()
    result_str = lower_str.replace(" ", "-")
    return result_str


def safe_index(lst: List[Any], item: Any, default: Any = None) -> int:
    try:
        return lst.index(item)
    except ValueError:
        return default


def hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()
