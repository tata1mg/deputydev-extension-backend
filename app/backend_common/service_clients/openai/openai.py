from typing import Any, Dict, List, Optional

import httpx
from deputydev_core.utils.singleton import Singleton
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from torpedo import CONFIG

config = CONFIG.config


class OpenAIServiceClient(metaclass=Singleton):
    def __init__(self):
        self.__client = AsyncOpenAI(
            api_key=config.get("OPENAI_KEY"),
            timeout=config.get("OPENAI_TIMEOUT"),
            http_client=httpx.AsyncClient(
                timeout=config.get("OPENAI_TIMEOUT"),
                limits=httpx.Limits(
                    max_connections=1000,
                    max_keepalive_connections=100,
                    keepalive_expiry=20,
                ),
            ),
        )

    async def get_llm_response(
        self,
        conversation_messages: List[Dict[str, Any]],
        model: str,
        tool_choice: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_type: str = "json_object",
    ) -> ChatCompletion:
        completion = await self.__client.chat.completions.create(
            model=model,
            response_format={"type": response_type},
            messages=conversation_messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=0.5,
        )
        # we need both message and output token now to returning full completion message
        return completion

    async def create_embedding(self, input, model: str, encoding_format: str):
        embeddings = await self.__client.embeddings.create(
            input=input, model=model, encoding_format=encoding_format, timeout=2
        )
        return embeddings
