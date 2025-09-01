from app.backend_common.service_clients.base_scm_client import BaseSCMClient
from app.backend_common.utils.sanic_wrapper import CONFIG

config = CONFIG.config


class Base(BaseSCMClient):
    BASE_URL = config["CONFLUENCE"]["HOST"]
    PATH = config["CONFLUENCE"]["PATH"]
    AUTH_TOKEN = config["CONFLUENCE"]["AUTH_TOKEN"]
    USERNAME = config["CONFLUENCE"]["USERNAME"]
    TIMEOUT = config["CONFLUENCE"]["TIMEOUT"]
