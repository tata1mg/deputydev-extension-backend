from sanic.log import logger
from torpedo import CONFIG

from ...utils import service_client_wrapper
from ..base import Base


class LabsClient(Base):
    _lab_config = CONFIG.config["LABS"]
    _host = _lab_config["HOST"]
    _service_name = "Labs"
    _timeout = _lab_config["TIMEOUT"]

    @classmethod
    @service_client_wrapper(service_name=_service_name)
    async def get_lab_test_details(cls, test_details: dict):
        """
        This Function is responsible for getting lab test
        details based on lab test_id and city

        Args:
            test_details: dict containing test_id and city

        Returns:
            Dict containing lab test details

        """
        path = "/v1/test/{lab_id}".format(lab_id=test_details.pop("identifier"))
        headers = {
            "Content-Type": "application/json",
            # TODO: Why is this platform hardcoded here?
            "X-Platform": "Android-17.9.0",
            "X-Access-Key": "1mg_client_access_key",
        }
        try:
            result = await cls.get(
                path=path, query_params=test_details, headers=headers
            )
            return result.data

        except Exception as e:
            logger.error(
                """Unable to get lab test details from Labs bcoz {} """.format(e)
            )
            return {}
