from requests.auth import HTTPBasicAuth
from torpedo import CONFIG

config = CONFIG.config


class Base:
    BASE_URL = config["CONFLUENCE"]["HOST"]
    PATH = config["CONFLUENCE"]["PATH"]
    AUTH_TOKEN = config["CONFLUENCE"]["AUTH_TOKEN"]
    USERNAME = config["CONFLUENCE"]["USERNAME"]
    TIMEOUT = config["CONFLUENCE"]["TIMEOUT"]

    @classmethod
    def auth(cls):
        return HTTPBasicAuth(cls.USERNAME, cls.AUTH_TOKEN)
