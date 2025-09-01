import json
import logging
from typing import Any, Dict

from pythonjsonlogger import jsonlogger


class StructuredLoggingFormatter(jsonlogger.JsonFormatter):
    """Logging formatter for structured json logs.

    It extends `jsonlogger.JsonFormatter` that ensures that logs are structured json and
    each 'extra' key is converted to a attribute of json log.

    Additionally:
    - ensures message is string and puts a strict cap on string length for 2k chars ~ 100kb.
    - formats apm correlation ids
    - renames fields
    - removes redundant fields
    - removes logger name

    """  # noqa: E501

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datefmt = "%Y-%m-%dT%H:%M:%S"
        self.rename_fields = {
            "levelname": "loglevel",
            "asctime": "timestamp",
        }

    def format(self, record):
        """Formats a log record and serializes to json"""
        # serialize msg if dict
        if isinstance(record.msg, dict):
            record.msg = json.dumps(record.msg)
        return super().format(record)

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # remove logger name
        log_record.pop("name", "")

        # truncate (2000 chars ~ 100kb)
        if log_record.get("message") and len(log_record["message"]) > 2000:
            log_record["message"] = f"{log_record['message'][:2000]}..."

        # rename exc_info -> traceback
        log_record["traceback"] = log_record.pop("exc_info", None)
