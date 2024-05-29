from torpedo import CONFIG
from requests.auth import HTTPBasicAuth

config = CONFIG.config

class Base:
    BASE_URL = config['ATLASSIAN']['HOST']
    V3_PATH = config['ATLASSIAN']['V3_PATH']
    AUTH_TOKEN = config['ATLASSIAN']['AUTH_TOKEN']
    USERNAME = config['ATLASSIAN']['USERNAME']

    @classmethod
    def auth(cls):
        return HTTPBasicAuth(cls.USERNAME, cls.AUTH_TOKEN)
