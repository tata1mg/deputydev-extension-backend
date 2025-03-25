from typing import Optional

from aiobotocore.session import AioSession
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from types_aiobotocore_apigatewaymanagementapi import ApiGatewayManagementApiClient


class SocketClosedException(Exception):
    pass

class AWSAPIGatewayServiceClient:
    API_GATEWAY_MANAGEMENT_API_NAME = "apigatewaymanagementapi"

    def __init__(self, host: Optional[str] = None):
        self.host: str = host or ConfigManager.configs["AWS_API_GATEWAY"]["HOST"]

    async def post_to_endpoint_connection(self, endpoint: str, connection_id: str, message: str):
        """
        Send message to the connection_id for the given endpoint
        :param endpoint: str
        :param connection_id: str
        :param message: str

        :return: None
        """

        session = AioSession()

        client: ApiGatewayManagementApiClient = session.create_client(  # type: ignore
            self.API_GATEWAY_MANAGEMENT_API_NAME,  # type: ignore
            region_name=ConfigManager.configs["AWS_API_GATEWAY"]["AWS_REGION"],  # type: ignore
            endpoint_url=self.host + endpoint,  # type: ignore
        )  # type: ignore

        async with client as apigateway_client:
            try:
                await apigateway_client.post_to_connection(ConnectionId=connection_id, Data=message.encode("utf-8"))
            except client.exceptions.GoneException:
                raise SocketClosedException(f"Connection with connection_id: {connection_id} is closed")
            except Exception as _ex:
                AppLogger.log_error(
                    f"Error occurred while sending message to connection_id: {connection_id} for endpoint {endpoint}, ex: {_ex}"
                )
