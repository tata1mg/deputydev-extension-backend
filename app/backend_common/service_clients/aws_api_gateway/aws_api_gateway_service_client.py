from typing import Optional
from sanic.log import logger
from aiobotocore.session import AioSession
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from types_aiobotocore_apigatewaymanagementapi import ApiGatewayManagementApiClient
from time import time

class SocketClosedException(Exception):
    pass


class AWSAPIGatewayServiceClient:
    API_GATEWAY_MANAGEMENT_API_NAME = "apigatewaymanagementapi"

    def __init__(self, host: Optional[str] = None):
        self.host: str = host or ConfigManager.configs["AWS_API_GATEWAY"]["HOST"]
        self._client: ApiGatewayManagementApiClient | None = None

    async def init_client(self, endpoint: str):
        if self._client is not None:
            return
        session = AioSession()
        self._client = await session.create_client(
            service_name=self.API_GATEWAY_MANAGEMENT_API_NAME,
            region_name=ConfigManager.configs["AWS_API_GATEWAY"]["AWS_REGION"],
            endpoint_url=ConfigManager.configs["AWS_API_GATEWAY"]["HOST"] + endpoint,
        ).__aenter__()

    async def post_to_connection(self, connection_id: str, message: str):
        if self._client is None:
            raise RuntimeError("API Gateway client is not initialized. Call `init_client` first.")

        try:
            await self._client.post_to_connection(
                ConnectionId=connection_id,
                Data=message.encode("utf-8"),
            )
        except Exception as _ex:
            logger.error(
                f"[GatewayMessenger] Error sending message to {connection_id}: {_ex}"
            )
            raise SocketClosedException(f"Connection with connection_id: {connection_id} is closed")

    async def close(self):
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
            logger.info("[GatewayMessenger] API Gateway client closed")
