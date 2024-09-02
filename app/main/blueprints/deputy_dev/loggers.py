from sanic.log import logger

from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)


class AppLogger:
    @classmethod
    def log_info(cls, message):
        logger.info(f"{message} -- meta_info -- {cls.__get_meta_info()}")

    @classmethod
    def log_error(cls, message):
        logger.error(f"{message} -- meta_info -- {cls.__get_meta_info()}")

    @classmethod
    def log_warn(cls, message):
        logger.warn(f"{message} -- meta_info -- {cls.__get_meta_info()}")

    @classmethod
    def __get_meta_info(cls):
        meta_info = {
            "scm_pr_id": get_context_value("scm_pr_id"),
            "repo_name": get_context_value("repo_name"),
            "request_id": get_context_value("request_id"),
        }
        return meta_info
