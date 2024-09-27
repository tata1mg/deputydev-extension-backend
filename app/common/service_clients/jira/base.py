from torpedo import CONFIG

from app.common.service_clients.base_scm_client import BaseSCMClient

config = CONFIG.config


class Base(BaseSCMClient):
    BASE_URL = config["JIRA"]["HOST"]
    V3_PATH = config["JIRA"]["V3_PATH"]
    TIMEOUT = config["JIRA"]["TIMEOUT"] or 5
