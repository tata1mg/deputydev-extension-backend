from pathlib import Path
from typing import Any, Dict

import ujson
from sanic.log import error_logger


def json_file_to_dict(file: str) -> Dict[str, Any]:
    """Parse json file into a dict.

    Args:
        file (str): file to be parsed

    Returns:
        dict: parsed data
    """
    try:
        with Path(file).open() as config_file:
            config = ujson.load(config_file)
            return config

    except (TypeError, FileNotFoundError, ValueError) as exception:
        error_logger.exception("Failed to parse json file: %s", file)
        raise exception


class CONFIG:
    # NOTE: attribute with same name as class is a code smell
    # this is kept anyways for backward compatiblity.
    config: Dict[str, Any] = json_file_to_dict("./config.json")
