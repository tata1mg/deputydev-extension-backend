from typing import Any, AsyncIterator, Dict, List, Optional

from deputydev_core.utils.singleton import Singleton
from google import genai
from google.genai import errors, types
from google.oauth2 import service_account
from torpedo import CONFIG

from app.backend_common.service_clients.exceptions import GeminiThrottledError

config = CONFIG.config


class GeminiServiceClient(metaclass=Singleton):
    def __init__(self) -> None:
        credentials_dict = {
            "type": config["VERTEX"].get("type"),
            "project_id": config["VERTEX"].get("project_id"),
            "private_key_id": config["VERTEX"].get("private_key_id"),
            "private_key": config["VERTEX"].get("private_key"),
            "client_email": config["VERTEX"].get("client_email"),
            "client_id": config["VERTEX"].get("client_id"),
            "auth_uri": config["VERTEX"].get("auth_uri"),
            "token_uri": config["VERTEX"].get("token_uri"),
            "auth_provider_x509_cert_url": config["VERTEX"].get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": config["VERTEX"].get("client_x509_cert_url"),
            "universe_domain": config["VERTEX"].get("universe_domain"),
        }
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        self.client = genai.Client(
            http_options=types.HttpOptions(api_version="v1"),
            vertexai=True,
            credentials=credentials,
            project=credentials_dict["project_id"],
            location=config["VERTEX"].get("location"),
        )

    async def get_llm_non_stream_response(
        self,
        model_name: str,
        contents: List[types.Content],
        system_instruction: types.Part = None,
        tools: List[types.Tool] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.5,
        tool_config=None,  # noqa: ANN001
        response_mime_type: str = "text/plain",
        max_output_tokens: int = 8192,
    ) -> types.GenerateContentResponse:
        data = await self.client.aio.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
                temperature=temperature,
                response_mime_type=response_mime_type,
                response_schema=response_schema,
                max_output_tokens=max_output_tokens,
            ),
        )
        return data

    async def get_llm_stream_response(
        self,
        model_name: str,
        contents: List[types.Content],
        system_instruction: types.Part = None,
        tools: List[types.Tool] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.5,
        tool_config=None,  # noqa: ANN001
        response_mime_type: str = "text/plain",
        max_output_tokens: int = 8192,
    ) -> AsyncIterator[types.GenerateContentResponse]:
        try:
            base_stream = await self.client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=temperature,
                    response_mime_type=response_mime_type,
                    response_schema=response_schema,
                    max_output_tokens=max_output_tokens,
                ),
            )
        except errors.APIError as e:
            if e.code == 429:
                raise GeminiThrottledError(model=model_name, retry_after=None, detail=str(e)) from e
            raise

        return base_stream

    async def get_tokens(self, content: str, model_name: str) -> int:
        tokens = self.client.models.count_tokens(model=model_name, content=content)
        return tokens
