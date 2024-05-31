import hashlib
import operator
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

import mmh3
from packaging.version import Version
from sanic.log import logger
from torpedo import Task, TaskExecutor
from torpedo.common_utils import CONFIG

from app.constants import IGNORE_FILES, TimeFormat
from app.modules.tiktoken import TikToken

name_slug_pattern = re.compile(r"[^A-Za-z0-9.]")
name_slug_replace_string = "-"
name_slug_replace_multiple = re.compile(r"-+")
name_slug_replace_leading_trailing = re.compile(r"^-|-*$")


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


def get_slug_from_name(name):
    if not name:
        return None
    else:
        replaced_string = re.sub(
            name_slug_replace_leading_trailing,
            "",
            re.sub(
                name_slug_replace_multiple,
                name_slug_replace_string,
                re.sub(name_slug_pattern, name_slug_replace_string, name),
            ),
        )
        return replaced_string.lower()


def get_sku_url(sku_id, name, type):
    url = None
    if type == "otc":
        url = "/otc/{}-{}"
        sku_id = "{}{}".format("otc", sku_id)
        url = url.format(get_slug_from_name(name), sku_id)
    elif type in ("allopathy", "drugs"):
        url = "/drugs/{}-{}".format(get_slug_from_name(name), sku_id)
    return url


def check_feature_enabled_for_platform(feature_config, client_attributes):
    """
    @param feature_config: Feature name for which we need to check if filter's pass or fail
    @param client_attributes: dict containing client and platform for the user
    @return: True or False depending on client and version
    """
    operations = {
        "=": operator.eq,
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
    }
    client = client_attributes["client"].lower()
    app_version = client_attributes["client_version"] if "client_version" in client_attributes else "1.0.0"

    for criteria in feature_config:
        criteria_client = criteria["client"]
        criteria_operation = criteria["op"]
        if operations[criteria_operation](client, criteria_client):
            if criteria.get("version"):
                version_criteria = criteria["version"]["op"]
                version_required = criteria["version"]["number"]
                if operations[version_criteria](Version(app_version), Version(version_required)):
                    return True
            else:
                return True
    return False


def prepare_client_attributes(client, client_version=None, feature_name=""):
    """
    @param client: Name of the client platform
    @param client_version: dict containing client and platform for the user
    @param feature_name: Feature name for which check is implemented
    @return: dictionary of client attributes if exists, else None
    """
    client_attributes = {"client": client}
    if client_version:
        client_attributes["client_version"] = client_version
    else:
        logger.info("client version is required for {} check".format(feature_name))
        return None
    return client_attributes


def validate_eta_pincode(eta_pincode):
    """
    Check if given eta_pincode is valid
    Handles null value which is received as 'null' for eta_pincode query param
    """
    if not eta_pincode or str(eta_pincode).lower() == "null":
        return False
    return True


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


def request_logger(_request) -> str:
    headers = _request.headers
    logger.info(f"Entry: For request ID: {headers.get('X-REQUEST-ID')}, " f"for smart_code_review")
    return headers.get("X-REQUEST-ID")


def get_comment(payload):
    try:
        bb_payload = {}
        comment = payload["comment"]
        raw_content = remove_special_char("\\", comment["content"]["raw"])
        if "parent" in comment and "inline" in comment:
            bb_payload["comment"] = raw_content
            bb_payload["parent"] = comment["parent"]["id"]
            bb_payload["path"] = comment["inline"]["path"]
            return bb_payload
        elif "inline" in comment:
            bb_payload["comment"] = raw_content
            bb_payload["path"] = comment["inline"]["path"]
            bb_payload["line_number"] = comment["inline"]["to"]
            return bb_payload
        else:
            return {"comment": raw_content}
    except KeyError as e:
        raise f"Error: {e} not found in the JSON structure."
    except Exception as e:
        raise f"An unexpected error occurred: {e}"


def remove_special_char(char, input_string):
    return input_string.replace(char, "")


def add_corrective_code(data):
    # Check if corrective_code exists and is a dictionary
    if isinstance(data, dict):
        comment = data.get("comment", "")
        if data.get("corrective_code") and len(data.get("corrective_code")) > 0:
            comment += data.get("corrective_code", "")
        return comment
    elif isinstance(data, str):
        return data
    else:
        return ""


def ignore_files(response):
    resp_text = ""
    for d in response.text.split("diff --git "):
        if not any(keyword in d for keyword in IGNORE_FILES):
            resp_text += d
    return resp_text


def calculate_total_diff(diff):
    total_lies = 0
    chunks = diff.split("@@")
    for chunk in chunks[1:]:
        lines = chunk.split("\n")
        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                total_lies += 1
            elif line.startswith("-") and not line.startswith("---"):
                total_lies += 1
    return total_lies


def parse_collection_name(name: str) -> str:
    # Replace any non-alphanumeric characters with hyphens
    name = re.sub(r"[^\w-]", "--", name)
    # Ensure the name is between 3 and 63 characters and starts/ends with alphanumeric
    name = re.sub(r"^(-*\w{0,61}\w)-*$", r"\1", name[:63].ljust(3, "x"))
    return name


def hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def build_openai_conversation_message(system_message, user_message) -> list:
    """
    Build the conversation message list to be passed to openai.
    """
    message = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
    return message


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


def get_filtered_response(response: dict, confidence_filter_score: float) -> bool:
    """
    Filters the response based on the given confidence filter score.

    Args:
        response (Dict[str, Any]): The response dictionary containing a confidence score.
        confidence_filter_score (float): The threshold confidence score for filtering.

    Returns:
        bool: whether the response passes check or not.

    """
    confidence_score = response.get("confidence_score")
    return response.get("comment") and float(confidence_score) >= float(confidence_filter_score)


def get_request_time() -> str:
    """
    Returns request time in str format
    """
    # Get the current datetime in UTC timezone
    current_datetime = datetime.now(timezone.utc)
    # Format the datetime as per the specified format
    formatted_datetime_str = current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    return str(formatted_datetime_str)
