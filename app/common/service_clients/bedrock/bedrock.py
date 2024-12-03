from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from torpedo import CONFIG


class BedrockServiceClient:
    def __init__(self):
        self.client = None

    async def get_llm_response(self, formatted_conversation: str, model: str = None) -> dict:
        response = await self.invoke_botocore_client(formatted_conversation, model)
        return response

    async def invoke_botocore_client(self, formatted_conversation, model):
        session = get_session()
        config = AioConfig(read_timeout=CONFIG.config["AWS"]["BEDROCK_READ_TIMEOUT"])
        async with session.create_client(
            service_name=CONFIG.config["AWS"]["BEDROCK_SERVICE_NAME"],
            aws_access_key_id=CONFIG.config["AWS"].get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=CONFIG.config["AWS"].get("AWS_SECRET_ACCESS_KEY"),
            # aws_session_token=CONFIG.config["AWS"].get("AWS_SESSION_TOKEN"),
            region_name=CONFIG.config["AWS"]["AWS_REGION"],
            config=config,
        ) as client:
            response = await client.invoke_model(modelId=model, body=formatted_conversation)
            return response
