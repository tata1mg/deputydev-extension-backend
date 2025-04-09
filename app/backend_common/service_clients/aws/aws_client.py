from aiobotocore.config import AioConfig
from aiobotocore.endpoint import MAX_POOL_CONNECTIONS
from aiobotocore.session import AioSession, ClientCreatorContext, get_session

from app.backend_common.utils.types.aws import AWSErrorMessages


class AWSClient:
    DEFAULT_TIMEOUT_IN_SECONDS = 10

    @classmethod
    async def create_client(
        cls, aws_service_name: str, region_name: str, aws_secret_access_key=None, aws_access_key_id=None, **kwargs
    ) -> ClientCreatorContext:
        try:
            session: AioSession = get_session()

            connect_timeout = kwargs.get("connect_timeout") or cls.DEFAULT_TIMEOUT_IN_SECONDS
            read_timeout = kwargs.get("read_timeout") or cls.DEFAULT_TIMEOUT_IN_SECONDS
            signature_version = kwargs.get("signature_version", None)
            endpoint_url = kwargs.get("endpoint_url")
            max_pool_connections = kwargs.get("max_pool_connections") or MAX_POOL_CONNECTIONS

            config = AioConfig(
                connect_timeout=connect_timeout,
                read_timeout=read_timeout,
                signature_version=signature_version,
                max_pool_connections=max_pool_connections,
            )
            client_args = {
                "service_name": aws_service_name,
                "region_name": region_name,
                "config": config,
                "endpoint_url": endpoint_url,
                "aws_secret_access_key": aws_secret_access_key,
                "aws_access_key_id": aws_access_key_id,
            }
            client: ClientCreatorContext = session.create_client(**client_args)
            return client
        except Exception as error:
            raise Exception(AWSErrorMessages.AwsConnectionError.value.format(error=error))
