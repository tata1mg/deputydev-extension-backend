import google.generativeai as genai
from deputydev_core.utils.singleton import Singleton
from openai.types.chat import ChatCompletionMessage
from app.backend_common.utils.sanic_wrapper import CONFIG

config = CONFIG.config


class GeminiProServiceClient(metaclass=Singleton):
    def __init__(self):
        genai.configure(api_key=config.get("GOOGLE_API_KEY"))
        self.client = genai.GenerativeModel(
            "gemini-pro",
            generation_config={
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            },
        )

    def get_response(self, final_prompt) -> ChatCompletionMessage:
        response = self.client.generate_content(final_prompt)
        return response.text
