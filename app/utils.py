import operator
import re
import time

import mmh3
from packaging.version import Version
from sanic.log import logger
from torpedo.common_utils import CONFIG

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
