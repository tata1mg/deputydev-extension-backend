import requests
from sanic.log import logger

from .base import Base


class Issue(Base):
    ISSUE_PATH = "/issue"

    @classmethod
    async def get(cls, issue_id: int, fields: str = None):

        # returns no response if issue_id is not present
        if not issue_id:
            return {}

        url = f"{cls.BASE_URL}{cls.V3_PATH}{cls.ISSUE_PATH}/{issue_id}"
        query_params = {}
        if fields:
            query_params["fields"] = fields
        try:
            response = requests.get(url, auth=cls.auth(), params=query_params, timeout=cls.TIMEOUT)
            return response.json()
        except Exception as e:
            logger.error("Exception occurred while fetching issue details from jira: {}".format(e))
        return {}
