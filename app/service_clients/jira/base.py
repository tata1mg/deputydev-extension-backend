from requests.auth import HTTPBasicAuth
from torpedo import CONFIG

config = CONFIG.config


class Base:
    BASE_URL = config["JIRA"]["HOST"]
    V3_PATH = config["JIRA"]["V3_PATH"]
    AUTH_TOKEN = config["JIRA"]["AUTH_TOKEN"]
    USERNAME = config["JIRA"]["USERNAME"]
    TIMEOUT = config["JIRA"]["TIMEOUT"] or 5

    @classmethod
    def auth(cls):
        return HTTPBasicAuth(cls.USERNAME, cls.AUTH_TOKEN)
