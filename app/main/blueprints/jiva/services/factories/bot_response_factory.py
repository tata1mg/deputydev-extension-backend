from app.backend_common.utils.headers import Headers
from app.main.blueprints.jiva.models.chat import ChatModel
from app.main.blueprints.jiva.services.google.gemini_response import GeminiAiResponse
from app.main.blueprints.jiva.services.google.gemini_vision_response import (
    GeminiVisionAiResponse,
)
from app.main.blueprints.jiva.services.openai.openai_response import OpenAiResponse


class BotResponseFactory:
    BOT_FACTORY = {"diagnostics_query": OpenAiResponse, "pdf": GeminiAiResponse, "image": GeminiVisionAiResponse}

    @classmethod
    async def get_bot_response(cls, payload: ChatModel.ChatRequestModel, headers: Headers):
        kclass = cls.BOT_FACTORY.get(payload.chat_type)
        response = await kclass().get_response(payload, headers)
        return response
