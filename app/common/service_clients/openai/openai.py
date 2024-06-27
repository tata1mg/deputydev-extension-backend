import httpx
from commonutils.utils import Singleton
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from torpedo import CONFIG

from app.main.blueprints.jiva.services.openai.util import get_openai_funcs

config = CONFIG.config


class OpenAIServiceClient(metaclass=Singleton):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=config.get("OPENAI_KEY"),
            timeout=60,
            http_client=httpx.AsyncClient(
                timeout=60,
                limits=httpx.Limits(
                    max_connections=1000,
                    max_keepalive_connections=100,
                    keepalive_expiry=20,
                ),
            ),
        )

    async def get_response(self, conversation_messages) -> ChatCompletionMessage:
        completion = await self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=conversation_messages,
            tools=get_openai_funcs(),
            tool_choice="auto",
            temperature=0.5,
        )
        return completion.choices[0].message
