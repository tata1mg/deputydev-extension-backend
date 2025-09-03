from app.backend_common.service_clients.base_scm_client import BaseSCMClient
from app.backend_common.utils.sanic_wrapper import CONFIG

config = CONFIG.config


class Base(BaseSCMClient):
    BASE_URL = config["JIRA"]["HOST"]
    V3_PATH = config["JIRA"]["V3_PATH"]
    TIMEOUT = config["JIRA"]["TIMEOUT"] or 5
