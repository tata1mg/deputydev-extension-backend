from .base import Base
import requests

class Issue(Base):
    ISSUE_PATH = '/issue'

    @classmethod
    async def get(cls, issue_id, fields):
        url = f"{cls.BASE_URL}{cls.V3_PATH}{cls.ISSUE_PATH}/{issue_id}"
        query_params = {"fields": fields}
        response = requests.get(url, auth=cls.auth(), params=query_params)
        return response.json()
