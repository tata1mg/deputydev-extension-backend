import urllib.request
from io import BytesIO

import ujson
from PIL import Image

from app.backend_common.service_clients.gemini.gemini_vision import (
    GeminiVisionServiceClient,
)
from app.backend_common.constants.error_messages import ErrorMessages
from app.backend_common.utils.headers import Headers
from app.main.blueprints.jiva.models.chat import ChatModel, ChatTypeMsg
from app.main.blueprints.jiva.services.bots.utils import generate_prompt


class GeminiVisionAiResponse:
    def __init__(self):
        self.client = GeminiVisionServiceClient()

    async def get_response(self, payload: ChatModel.ChatRequestModel, headers: Headers):
        image_data = self.download_image(payload.file_url)
        if not image_data:
            return ChatModel.ChatResponseModel(
                chat_id=payload.chat_id,
                data=[
                    ChatTypeMsg.model_validate(
                        {
                            "answer": ErrorMessages.RETRIEVAL_FAIL_MSG.value,
                        }
                    )
                ],
            )
        final_prompt = generate_prompt(payload)
        llm_response = self.client.get_response([final_prompt, image_data])
        return self.generate_response(payload.chat_id, llm_response)

    @staticmethod
    def download_image(image_url):
        try:
            with urllib.request.urlopen(image_url) as response:
                image_data = response.read()
                return Image.open(BytesIO(image_data))
        except urllib.error.URLError:
            return None

    @staticmethod
    def generate_response(chat_id: str, llm_response) -> ChatModel.ChatResponseModel:
        """
        Generate response for LLM.
        @param chat_id: Chat id of the conversation
        @param llm_response: Response received from LLM
        @return: Formatted response to be sent to client
        """
        return ChatModel.ChatResponseModel(chat_id=chat_id, data=[ChatTypeMsg(**ujson.loads(llm_response))])
