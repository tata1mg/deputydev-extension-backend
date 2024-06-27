from torpedo import CONFIG

from ...utils.app_utils import service_client_wrapper
from ..base import Base


class SearchClient(Base):
    _search_config = CONFIG.config["SEARCH"]
    _host = _search_config["HOST"]
    _service_name = "Search"
    _timeout = _search_config["TIMEOUT"]

    @classmethod
    @service_client_wrapper(service_name=_service_name)
    async def sku_by_ids(cls, payload, headers):
        path = "/v1/skus/by_ids"
        result = await cls.post(path, data=payload, headers=headers)
        return result.data
