import json
from typing import Any, Dict, Optional, Tuple

from aiobotocore.config import AioConfig  # type: ignore
from aiobotocore.session import get_session  # type: ignore
from botocore.exceptions import ClientError
from types_aiobotocore_bedrock_runtime import BedrockRuntimeClient
from types_aiobotocore_bedrock_runtime.type_defs import (
    InvokeModelResponseTypeDef,
    InvokeModelWithResponseStreamResponseTypeDef,
)

from app.backend_common.service_clients.exceptions import AnthropicThrottledError
from app.backend_common.utils.sanic_wrapper import CONFIG  # type: ignore


class BedrockServiceClient:
    def __init__(self, region_name: str) -> None:
        self.client: Optional[BedrockRuntimeClient] = None
        self.region_name = region_name

    def _get_bedrock_client(self) -> BedrockRuntimeClient:
        session = get_session()
        config = AioConfig(read_timeout=CONFIG.config["AWS"]["BEDROCK_READ_TIMEOUT"])  # type: ignore
        self.client = session.create_client(  # type: ignore
            service_name=CONFIG.config["AWS"]["BEDROCK_SERVICE_NAME"],  # type: ignore
            aws_access_key_id=CONFIG.config["AWS"].get("ACCESS_KEY_ID"),  # type: ignore
            aws_secret_access_key=CONFIG.config["AWS"].get("SECRET_ACCESS_KEY"),  # type: ignore
            aws_session_token=CONFIG.config["AWS"].get("SESSION_TOKEN"),  # type: ignore
            region_name=self.region_name,  # type: ignore
            config=config,  # type: ignore
        )

        if not self.client:
            raise ValueError("Failed to create Bedrock client")
        return self.client

    async def get_llm_non_stream_response(self, llm_payload: Dict[str, Any], model: str) -> InvokeModelResponseTypeDef:
        bedrock_client = self._get_bedrock_client()
        async with bedrock_client as client:
            response = await client.invoke_model(modelId=model, body=json.dumps(llm_payload))
            return response

    async def get_llm_stream_response(
        self, llm_payload: Dict[str, Any], model: str
    ) -> Tuple[InvokeModelWithResponseStreamResponseTypeDef, BedrockRuntimeClient]:
        bedrock_client = await self._get_bedrock_client().__aenter__()
        try:
            response = await bedrock_client.invoke_model_with_response_stream(
                modelId=model, body=json.dumps(llm_payload)
            )
            return response, bedrock_client
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if code == "ThrottlingException" or status == 429:
                await bedrock_client.__aexit__(None, None, None)
                raise AnthropicThrottledError(
                    model=model, region=self.region_name, retry_after=None, detail=str(e)
                ) from e
            await bedrock_client.__aexit__(None, None, None)
            raise e
        except Exception as e:
            await bedrock_client.__aexit__(None, None, None)
            raise e
