from sanic.log import logger

from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)


class AppLogger:
    @classmethod
    def build_message(cls, message):
        return f"{cls.__get_meta_info()} -- message -- {message}"

    @classmethod
    def log_info(cls, message):
        logger.info(cls.build_message(message))

    @classmethod
    def log_error(cls, message):
        logger.error(cls.build_message(message))

    @classmethod
    def log_warn(cls, message):
        logger.warn(cls.build_message(message))

    @classmethod
    def __get_meta_info(cls):
        meta_info = {
            "team_id": get_context_value("team_id"),
            "scm_pr_id": get_context_value("scm_pr_id"),
            "repo_name": get_context_value("repo_name"),
            "request_id": get_context_value("request_id"),
        }
        return meta_info
