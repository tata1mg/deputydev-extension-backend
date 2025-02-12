import json
from typing import Any, Dict

from aiobotocore.config import AioConfig  # type: ignore
from aiobotocore.session import get_session  # type: ignore
from torpedo import CONFIG  # type: ignore
from types_aiobotocore_bedrock_runtime import BedrockRuntimeClient
from types_aiobotocore_bedrock_runtime.type_defs import InvokeModelResponseTypeDef


class BedrockServiceClient:
    def __init__(self):
        self.client = None

    async def get_llm_response(self, llm_payload: Dict[str, Any], model: str) -> InvokeModelResponseTypeDef:
        session = get_session()
        config = AioConfig(read_timeout=CONFIG.config["AWS"]["BEDROCK_READ_TIMEOUT"])  # type: ignore
        bedrock_client: BedrockRuntimeClient = session.create_client(  # type: ignore
            service_name=CONFIG.config["AWS"]["BEDROCK_SERVICE_NAME"],  # type: ignore
            aws_access_key_id=CONFIG.config["AWS"].get("AWS_ACCESS_KEY_ID"),  # type: ignore
            aws_secret_access_key=CONFIG.config["AWS"].get("AWS_SECRET_ACCESS_KEY"),  # type: ignore
            aws_session_token=CONFIG.config["AWS"].get("AWS_SESSION_TOKEN"),  # type: ignore
            region_name=CONFIG.config["AWS"]["AWS_REGION"],  # type: ignore
            config=config,  # type: ignore
        )
        async with bedrock_client as client:
            response = await client.invoke_model(modelId=model, body=json.dumps(llm_payload))
            return response
