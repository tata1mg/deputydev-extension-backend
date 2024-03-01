from app.models.chat import ChatModel
from app.managers.bots.openai_response import OpenAiResponse
from app.routes.end_user.headers import Headers
from app.managers.bots.gemini_response import GeminiAiResponse
from app.managers.bots.gemini_vision_response import GeminiVisionAiResponse


class BotResponseFactory:
    BOT_FACTORY = {
        "diagnostics_query": OpenAiResponse,
        "pdf": GeminiAiResponse,
        "image": GeminiVisionAiResponse
    }

    @classmethod
    async def get_bot_response(cls, payload: ChatModel.ChatRequestModel, headers: Headers):
        kclass = cls.BOT_FACTORY.get(payload.chat_type)
        response = await kclass().get_response(payload, headers)
        return response

