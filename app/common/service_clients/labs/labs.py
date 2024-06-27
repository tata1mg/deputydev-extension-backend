from sanic.log import logger
from torpedo import CONFIG

from ...utils.app_utils import service_client_wrapper
from ..base import Base


class LabsClient(Base):
    _lab_config = CONFIG.config["LABS"]
    _host = _lab_config["HOST"]
    _service_name = "Labs"
    _timeout = _lab_config["TIMEOUT"]

    @classmethod
    @service_client_wrapper(service_name=_service_name)
    async def get_lab_sku_details(cls, identifier: str, city: str):
        """
        This Function is responsible for getting lab test
        details based on lab test_id and city
        @param identifier: Lab test ID
        @param city: City name
        @return:
        """
        path = "/v1/test/{lab_id}".format(lab_id=identifier)
        headers = {
            "Content-Type": "application/json",
            "X-Platform": "Android-17.9.0",
            "X-Access-Key": "1mg_client_access_key",
        }
        try:
            result = await cls.get(path=path, query_params={"city": city}, headers=headers)
            return result.data

        except Exception as e:
            logger.error(
                f"Unable to get lab test details from Labs for test id: {identifier} and city: {city} , "
                f"Exception: {e}"
            )
