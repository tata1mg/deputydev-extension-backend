import requests
from sanic.log import logger

from .base import Base


class Page(Base):
    ISSUE_PATH = "/content"

    @classmethod
    async def get(cls, document_id):
        if document_id:
            url = f"{cls.BASE_URL}{cls.PATH}{cls.ISSUE_PATH}/{document_id}"
            query_params = {"expand": "body.storage,body.view"}
            try:
                response = requests.get(url, auth=cls.auth(), params=query_params, timeout=cls.TIMEOUT)
                return response.json()
            except Exception as e:
                logger.error("Exception occured while fetching issue details from jira: {}".format(e))
                return {}
        else:
            return {}
